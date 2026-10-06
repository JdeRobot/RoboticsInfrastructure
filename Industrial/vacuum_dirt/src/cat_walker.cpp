#include <algorithm>
#include <atomic>
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
#include <gz/msgs/stringmsg.pb.h>
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
// Mess the cat leaves alone once this much of it is still on the floor
constexpr int kMaxMess = 400;
const char *const kCatDirt[] = {"paw", "litter", "fur"};
constexpr double kFleeSpeed = 0.6;
constexpr double kTurnRate = 3.0;
// Distance covered by one loop of the walk animation
constexpr double kCycleDistance = 0.32;
constexpr double kFleeDistance = 0.7;
constexpr double kSafeDistance = 1.6;
constexpr double kSourceRadius = 0.25;
constexpr int kDirtyPrints = 36;
// Chance of heading to the pot or the litter box with clean or dirty paws
constexpr double kSourceChanceClean = 0.55;
constexpr double kSourceChanceDirty = 0.15;
constexpr int kKickedGrains = 30;
// Hair shed while resting, and now and then while walking
constexpr double kFurRestMin = 1.5;
constexpr double kFurRestMax = 3.5;
constexpr double kFurWalkChance = 0.3;
constexpr double kFurWalkEvery = 2.5;

// Palette indexes of vacuum_dirt.cpp
constexpr int kBrown = 24;
constexpr int kBeige = 26;
constexpr int kGrey = 28;
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
// sits for a while and runs away when the vacuum robot gets close. It keeps
// making a mess for the vacuum_dirt system to clean, published on
// <dirt_topic>:
//  - stepping on the soil of the spilled pot (<mud>) leaves muddy paw prints
//  - using the litter box (<litter>, box center at <litter_box>) kicks litter
//    out and leaves sandy paw prints
//  - it sheds hair where it rests and now and then while walking
// With clean paws it is more likely to head back to the pot or the box.
// It reads the progress on <score_topic> and, while more than <max_mess>
// pieces of its own dirt are left, it just strolls around without making
// any more, so the world never fills up if the robot can't keep up.
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
    scoreTopic = _sdf->Get<std::string>("score_topic", scoreTopic).first;
    maxMess = _sdf->Get<int>("max_mess", kMaxMess).first;
    mudSpot = _sdf->Get<math::Vector2d>("mud", mudSpot).first;
    litterSpot = _sdf->Get<math::Vector2d>("litter", litterSpot).first;
    litterBox = _sdf->Get<math::Vector2d>("litter_box", litterBox).first;
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
    node.Subscribe(scoreTopic, &CatWalker::OnScore, this);
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
    Move(now, dt);
    Apply(dt, _ecm);
    PublishDirt();
  }

private:
  enum class State { Idle, Walk, Flee };

  // Pieces of the cat's own dirt still on the floor, from the vacuum_dirt
  // JSON: "<category>":{"total":N,"collected":M}
  void OnScore(const msgs::StringMsg &_msg)
  {
    const std::string &json = _msg.data();
    int left = 0;
    for (const char *name : kCatDirt)
    {
      auto at = json.find("\"" + std::string(name) + "\":{");
      if (at == std::string::npos)
        continue;
      auto total = json.find("\"total\":", at);
      auto collected = json.find("\"collected\":", at);
      if (total == std::string::npos || collected == std::string::npos)
        continue;
      left += std::atoi(json.c_str() + total + 8) -
        std::atoi(json.c_str() + collected + 12);
    }
    messLeft = left;
  }

  bool Tidy() const
  {
    return messLeft >= maxMess;
  }

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
    dirtyPrints = 0;
    atSource = false;
    furAt = 0.0;
    sinceLastFur = 0.0;
    sinceLastPrint = 0.0;
    leftPaw = false;
    dirt.Clear();
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
      double toSource = Tidy() ? 0.0 :
        dirtyPrints > 0 ? kSourceChanceDirty : kSourceChanceClean;
      Vector2d goal = u(rng) < toSource ? (u(rng) < 0.5 ? mudSpot : litterSpot) :
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

  void Move(double _now, double _dt)
  {
    VisitSources();

    if (state == State::Idle || path.empty())
    {
      speed = 0.0;
      if (_now >= furAt && !Tidy())
      {
        std::uniform_real_distribution<double> every(kFurRestMin, kFurRestMax);
        furAt = _now + every(rng);
        Shed(0.08, 0.25);
      }
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

    sinceLastFur += step;
    if (sinceLastFur >= kFurWalkEvery && !Tidy())
    {
      sinceLastFur = 0.0;
      std::uniform_real_distribution<double> u(0, 1);
      if (u(rng) < kFurWalkChance)
        Shed(0.0, 0.05);
    }

    if (dirtyPrints > 0 && !Tidy())
    {
      sinceLastPrint += step;
      if (sinceLastPrint >= kPrintStep)
      {
        sinceLastPrint = 0.0;
        leftPaw = !leftPaw;
        double side = leftPaw ? kPrintSide : -kPrintSide;
        Vector2d at = pos + Vector2d(-std::sin(yaw), std::cos(yaw)) * side;
        Drop("paw paw 0.04 0.04", printColor + (leftPaw ? 1 : 0), at, yaw);
        --dirtyPrints;
      }
    }
  }

  // Dirty paws on the pot soil, litter kicked out of the box
  void VisitSources()
  {
    bool atMud = pos.Distance(mudSpot) < kSourceRadius;
    bool atLitter = pos.Distance(litterSpot) < kSourceRadius;
    if (atMud || atLitter)
    {
      dirtyPrints = kDirtyPrints;
      printColor = atMud ? kBrown : kBeige;
    }
    if (atLitter && !atSource && !Tidy())
    {
      // Thrown out of the box, mostly towards the room
      Vector2d out = (litterSpot - litterBox).Normalized();
      double base = std::atan2(out.Y(), out.X());
      std::normal_distribution<double> spread(0.0, 0.7);
      std::uniform_real_distribution<double> dist(0.0, 0.45);
      std::uniform_real_distribution<double> size(0.005, 0.009);
      for (int k = 0; k < kKickedGrains; ++k)
      {
        double a = base + spread(rng);
        Vector2d at = litterSpot + Vector2d(std::cos(a), std::sin(a)) * dist(rng);
        if (!Free(at))
          continue;
        double d = size(rng);
        Drop("litter disc " + std::to_string(d) + " " + std::to_string(d),
          kBeige + k % 2, at, 0.0);
      }
    }
    atSource = atMud || atLitter;
  }

  void Shed(double _minDist, double _maxDist)
  {
    std::uniform_real_distribution<double> dist(_minDist, _maxDist);
    std::uniform_real_distribution<double> angle(-M_PI, M_PI);
    for (int k = 0; k < 2; ++k)
    {
      double a = angle(rng);
      Vector2d at = pos + Vector2d(std::cos(a), std::sin(a)) * dist(rng);
      if (Free(at))
        Drop("fur fur 0.03 0.0025", kGrey + k, at, angle(rng));
    }
  }

  // Dirt name is "category shape size_x size_y" plus the color
  void Drop(const std::string &_what, int _color, const Vector2d &_at,
            double _yaw)
  {
    auto *p = dirt.add_pose();
    p->set_name(_what + " " + std::to_string(_color));
    msgs::Set(p, Pose3d(_at.X(), _at.Y(), 0, 0, 0, _yaw));
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

  void PublishDirt()
  {
    if (dirt.pose_size() == 0)
      return;
    dirtPub.Publish(dirt);
    dirt.Clear();
  }

  // Length of the exported animation loops (40 frames at 24 fps)
  static constexpr double kCycleLength{40.0 / 24.0};

  std::string actorName{"cat"};
  std::string robotName{"vacuum_cleaner"};
  std::string dirtTopic{"/vacuum_dirt/add"};
  std::string scoreTopic{"/vacuum_dirt/score"};
  int maxMess{kMaxMess};
  std::atomic<int> messLeft{0};
  Vector2d mudSpot{0, 0};
  Vector2d litterSpot{0, 0};
  Vector2d litterBox{0, 0};
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

  int dirtyPrints{0};
  int printColor{kBrown};
  bool atSource{false};
  double sinceLastPrint{0.0};
  bool leftPaw{false};
  double furAt{0.0};
  double sinceLastFur{0.0};
  msgs::Pose_V dirt;

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
