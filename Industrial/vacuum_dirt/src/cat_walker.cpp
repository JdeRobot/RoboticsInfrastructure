#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <queue>
#include <random>
#include <string>
#include <vector>

#include <gz/common/Console.hh>
#include <gz/common/Util.hh>
#include <gz/math/Pose3.hh>
#include <gz/math/Vector2.hh>
#include <gz/msgs/pose_v.pb.h>
#include <gz/msgs/Utility.hh>
#include <gz/plugin/Register.hh>
#include <gz/sim/Actor.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/Actor.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/transport/Node.hh>

using namespace gz;
using namespace sim;
using math::Pose3d;
using math::Vector2d;

namespace vacuum_dirt
{

namespace
{
constexpr double kWalkSpeed = 0.28;
constexpr double kFleeSpeed = 0.6;
constexpr double kTurnRate = 3.0;
// Distance covered by one loop of the walk animation
constexpr double kCycleDistance = 0.32;
constexpr double kFleeDistance = 0.7;
constexpr double kSafeDistance = 1.6;
constexpr double kMudRadius = 0.25;
constexpr int kMudPrints = 36;
// Cats put the hind paw where the front one was, so a walk leaves a single
// zigzag line of prints
constexpr double kPrintStep = 0.11;
constexpr double kPrintSide = 0.035;

double Wrap(double _a)
{
  return std::atan2(std::sin(_a), std::cos(_a));
}
}  // namespace

// Moves a cat actor around the house. It strolls between random spots,
// sits for a while, runs away when the vacuum robot gets close and now and
// then walks back to a spilled plant pot. Right after stepping on the soil
// its paws are muddy, and every step leaves a paw print that is published
// on <dirt_topic> for the vacuum_dirt system to draw and count.
//
// The walkable area is a PGM map (dark = free) with its lower left corner at
// <origin_x>/<origin_y> and <resolution> meters per pixel.
class CatWalker:
  public System,
  public ISystemConfigure,
  public ISystemPreUpdate,
  public ISystemReset
{
public:
  void Configure(
    const Entity &,
    const std::shared_ptr<const sdf::Element> &_sdf,
    EntityComponentManager &,
    EventManager &) override
  {
    actorName = _sdf->Get<std::string>("actor", actorName).first;
    robotName = _sdf->Get<std::string>("robot", robotName).first;
    dirtTopic = _sdf->Get<std::string>("dirt_topic", dirtTopic).first;
    mudSpot = _sdf->Get<math::Vector2d>("mud", mudSpot).first;
    auto start = _sdf->Get<math::Vector3d>("start",
      math::Vector3d(mudSpot.X(), mudSpot.Y(), 0)).first;
    startPos = Vector2d(start.X(), start.Y());
    startYaw = start.Z();

    std::string map = common::findFile(_sdf->Get<std::string>("map"));
    if (!LoadMap(map, _sdf->Get<double>("resolution", 0.05).first,
                 _sdf->Get<double>("origin_x", 0.0).first,
                 _sdf->Get<double>("origin_y", 0.0).first))
    {
      gzerr << "cat_walker: could not load map [" << map << "]\n";
      return;
    }

    dirtPub = node.Advertise<msgs::Pose_V>(dirtTopic);
    ready = true;
    Restart();
  }

  void Reset(const UpdateInfo &, EntityComponentManager &) override
  {
    Restart();
  }

  void PreUpdate(const UpdateInfo &_info, EntityComponentManager &_ecm) override
  {
    if (!ready)
      return;

    if (actor == kNullEntity)
    {
      actor = _ecm.EntityByComponents(components::Name(actorName));
      if (!_ecm.Component<components::Actor>(actor))
      {
        actor = kNullEntity;
        return;
      }
    }

    double now = std::chrono::duration<double>(_info.simTime).count();
    double dt = std::clamp(now - lastTime, 0.0, 0.05);
    lastTime = now;
    if (_info.paused)
      return;

    UpdateRobot(_ecm);
    Think(now);
    Move(dt);
    Apply(dt, _ecm);
    PublishPrints();
  }

private:
  enum class State { Idle, Walk, Flee };

  void Restart()
  {
    pos = startPos;
    yaw = startYaw;
    path.clear();
    state = State::Idle;
    stateUntil = 0.0;
    retryAt = 0.0;
    lastTime = 0.0;
    animTime = 0.0;
    muddy = 0;
    sinceLastPrint = 0.0;
    leftPaw = false;
    prints.Clear();
    animation.clear();
    robot = kNullEntity;
    rng.seed(11);
  }

  bool LoadMap(const std::string &_file, double _res, double _ox, double _oy)
  {
    std::ifstream in(_file, std::ios::binary);
    if (!in)
      return false;
    auto skip = [&in]()
    {
      in >> std::ws;
      while (in.peek() == '#')
      {
        std::string line;
        std::getline(in, line);
        in >> std::ws;
      }
    };
    std::string magic;
    int maxval;
    in >> magic;
    skip();
    in >> width;
    skip();
    in >> height;
    skip();
    in >> maxval;
    in.get();
    if (magic != "P5" || width <= 0 || height <= 0)
      return false;

    std::vector<unsigned char> raw(width * height);
    in.read(reinterpret_cast<char *>(raw.data()), raw.size());
    res = _res;
    ox = _ox;
    oy = _oy;

    // First PGM row is the top of the map
    walkable.assign(raw.size(), false);
    for (int r = 0; r < height; ++r)
      for (int c = 0; c < width; ++c)
        walkable[Index(c, height - 1 - r)] = raw[r * width + c] < 128;

    for (int i = 0; i < width * height; ++i)
      if (walkable[i])
        freeCells.push_back(i);
    return !freeCells.empty();
  }

  int Index(int _x, int _y) const { return _y * width + _x; }

  bool Free(const Vector2d &_p) const
  {
    int x = static_cast<int>(std::floor((_p.X() - ox) / res));
    int y = static_cast<int>(std::floor((_p.Y() - oy) / res));
    return x >= 0 && y >= 0 && x < width && y < height &&
      walkable[Index(x, y)];
  }

  Vector2d Center(int _i) const
  {
    return Vector2d(ox + (_i % width + 0.5) * res,
                    oy + (_i / width + 0.5) * res);
  }

  bool Visible(const Vector2d &_a, const Vector2d &_b) const
  {
    double d = _a.Distance(_b);
    int n = std::max(1, static_cast<int>(d / (res * 0.5)));
    for (int k = 0; k <= n; ++k)
      if (!Free(_a + (_b - _a) * (static_cast<double>(k) / n)))
        return false;
    return true;
  }

  // A* over the grid, then shortcut by line of sight
  bool Plan(const Vector2d &_goal)
  {
    auto cellOf = [this](const Vector2d &_p)
    {
      int x = std::clamp(static_cast<int>((_p.X() - ox) / res), 0, width - 1);
      int y = std::clamp(static_cast<int>((_p.Y() - oy) / res), 0, height - 1);
      return Index(x, y);
    };
    int s = cellOf(pos);
    int g = cellOf(_goal);
    if (!walkable[g])
      return false;

    std::vector<double> cost(walkable.size(), 1e18);
    std::vector<int> from(walkable.size(), -1);
    using Item = std::pair<double, int>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> open;
    cost[s] = 0;
    open.push({0, s});
    auto h = [&](int _i)
    {
      return std::hypot(_i % width - g % width, _i / width - g / width);
    };
    while (!open.empty())
    {
      int cur = open.top().second;
      open.pop();
      if (cur == g)
        break;
      int cx = cur % width;
      int cy = cur / width;
      for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy)
        {
          int nx = cx + dx;
          int ny = cy + dy;
          if ((!dx && !dy) || nx < 0 || ny < 0 || nx >= width || ny >= height)
            continue;
          int n = Index(nx, ny);
          // Starting cell may be blocked if the cat was pushed off the map
          if (!walkable[n] && n != g)
            continue;
          double c = cost[cur] + std::hypot(dx, dy);
          if (c < cost[n])
          {
            cost[n] = c;
            from[n] = cur;
            open.push({c + h(n), n});
          }
        }
    }
    if (from[g] < 0)
      return false;

    std::vector<Vector2d> cells;
    for (int i = g; i != s && i >= 0; i = from[i])
      cells.push_back(Center(i));
    std::reverse(cells.begin(), cells.end());
    cells.back() = _goal;

    path.clear();
    Vector2d anchor = pos;
    for (size_t k = 0; k < cells.size(); ++k)
    {
      bool last = k + 1 == cells.size();
      if (last || !Visible(anchor, cells[k + 1]))
      {
        path.push_back(cells[k]);
        anchor = cells[k];
      }
    }
    return true;
  }

  Vector2d RandomSpot(double _minDist, double _maxDist,
                      const Vector2d &_awayFrom, double _awayDist)
  {
    std::uniform_int_distribution<size_t> pick(0, freeCells.size() - 1);
    for (int tries = 0; tries < 500; ++tries)
    {
      Vector2d p = Center(freeCells[pick(rng)]);
      double d = p.Distance(pos);
      if (d >= _minDist && d <= _maxDist &&
          p.Distance(_awayFrom) >= _awayDist)
        return p;
    }
    return Center(freeCells[pick(rng)]);
  }

  void UpdateRobot(EntityComponentManager &_ecm)
  {
    if (robot == kNullEntity || !_ecm.HasEntity(robot))
    {
      robot = _ecm.EntityByComponents(components::Model(),
        components::Name(robotName));
      if (robot == kNullEntity)
        return;
    }
    auto p = worldPose(robot, _ecm).Pos();
    robotPos = Vector2d(p.X(), p.Y());
  }

  void Think(double _now)
  {
    bool robotNear = robot != kNullEntity &&
      robotPos.Distance(pos) < kFleeDistance;

    if (_now < retryAt)
      return;

    if (robotNear && state != State::Flee)
    {
      if (Plan(RandomSpot(1.0, 3.0, robotPos, kSafeDistance)))
        state = State::Flee;
      else
        retryAt = _now + 0.5;
      return;
    }

    if (state == State::Idle && _now >= stateUntil)
    {
      std::uniform_real_distribution<double> u(0, 1);
      Vector2d goal = u(rng) < 0.35 ? mudSpot :
        RandomSpot(1.5, 1e9, robotPos, robot != kNullEntity ? kSafeDistance : 0);
      if (Plan(goal))
        state = State::Walk;
      else
        retryAt = _now + 0.5;
    }

    if (state != State::Idle && path.empty())
    {
      std::uniform_real_distribution<double> rest(3.0, 9.0);
      state = State::Idle;
      stateUntil = _now + rest(rng);
    }
  }

  void Move(double _dt)
  {
    if (pos.Distance(mudSpot) < kMudRadius)
      muddy = kMudPrints;

    if (state == State::Idle || path.empty())
    {
      speed = 0.0;
      return;
    }

    Vector2d to = path.front() - pos;
    if (to.Length() < 0.05)
    {
      path.erase(path.begin());
      return;
    }

    double target = std::atan2(to.Y(), to.X());
    double err = Wrap(target - yaw);
    double turn = std::clamp(err, -kTurnRate * _dt, kTurnRate * _dt);
    yaw = Wrap(yaw + turn);

    // Slow down while turning sharply so it doesn't moonwalk around corners
    double cruise = state == State::Flee ? kFleeSpeed : kWalkSpeed;
    speed = cruise * std::max(0.2, std::cos(err));
    double step = std::min(speed * _dt, to.Length());
    pos += Vector2d(std::cos(yaw), std::sin(yaw)) * step;
    animTime += step / kCycleDistance * kCycleLength;

    if (muddy > 0)
    {
      sinceLastPrint += step;
      if (sinceLastPrint >= kPrintStep)
      {
        sinceLastPrint = 0.0;
        leftPaw = !leftPaw;
        double side = leftPaw ? kPrintSide : -kPrintSide;
        Vector2d at = pos + Vector2d(-std::sin(yaw), std::cos(yaw)) * side;
        auto *p = prints.add_pose();
        p->set_name("paw");
        msgs::Set(p, Pose3d(at.X(), at.Y(), 0, 0, 0, yaw));
        --muddy;
      }
    }
  }

  void Apply(double _dt, EntityComponentManager &_ecm)
  {
    Actor cat(actor);
    std::string wanted = speed > 0.0 ? "walk" : "idle";
    if (wanted != animation)
    {
      cat.SetAnimationName(_ecm, wanted);
      _ecm.SetChanged(actor, components::AnimationName::typeId,
        ComponentState::OneTimeChange);
      animation = wanted;
    }
    if (speed == 0.0)
      animTime += _dt;

    cat.SetTrajectoryPose(_ecm, Pose3d(pos.X(), pos.Y(), 0, 0, 0, yaw));
    cat.SetAnimationTime(_ecm,
      std::chrono::duration_cast<std::chrono::steady_clock::duration>(
        std::chrono::duration<double>(animTime)));
    // The Actor setters don't flag the change so the GUI would never see it
    _ecm.SetChanged(actor, components::TrajectoryPose::typeId,
      ComponentState::PeriodicChange);
    _ecm.SetChanged(actor, components::AnimationTime::typeId,
      ComponentState::PeriodicChange);
  }

  void PublishPrints()
  {
    if (prints.pose_size() == 0)
      return;
    dirtPub.Publish(prints);
    prints.Clear();
  }

  // Length of the exported animation loops (40 frames at 24 fps)
  static constexpr double kCycleLength{40.0 / 24.0};

  std::string actorName{"cat"};
  std::string robotName{"vacuum_cleaner"};
  std::string dirtTopic{"/vacuum_dirt/add"};
  Vector2d mudSpot{0, 0};
  Vector2d startPos;
  double startYaw{0.0};

  int width{0};
  int height{0};
  double res{0.05};
  double ox{0.0};
  double oy{0.0};
  std::vector<bool> walkable;
  std::vector<int> freeCells;

  Entity actor{kNullEntity};
  Entity robot{kNullEntity};
  Vector2d robotPos{1e6, 1e6};

  State state{State::Idle};
  double stateUntil{0.0};
  // A failed plan is not retried right away, A* is too costly every step
  double retryAt{0.0};
  double lastTime{0.0};
  Vector2d pos;
  double yaw{0.0};
  double speed{0.0};
  double animTime{0.0};
  std::string animation;
  std::vector<Vector2d> path;

  int muddy{0};
  double sinceLastPrint{0.0};
  bool leftPaw{false};
  msgs::Pose_V prints;

  std::mt19937 rng{11};
  bool ready{false};

  transport::Node node;
  transport::Node::Publisher dirtPub;
};

}  // namespace vacuum_dirt

GZ_ADD_PLUGIN(
  vacuum_dirt::CatWalker,
  gz::sim::System,
  vacuum_dirt::CatWalker::ISystemConfigure,
  vacuum_dirt::CatWalker::ISystemPreUpdate,
  vacuum_dirt::CatWalker::ISystemReset)

GZ_ADD_PLUGIN_ALIAS(vacuum_dirt::CatWalker, "vacuum_dirt::CatWalker")
