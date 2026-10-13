#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <mutex>
#include <queue>
#include <random>
#include <sstream>
#include <string>
#include <unordered_map>
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
constexpr double kWalkSpeed = 0.5;
constexpr double kFleeSpeed = 1.0;
constexpr double kTurnRate = 6.0;
constexpr double kRestMin = 0.5;
constexpr double kRestMax = 2.5;
// Distance covered by one loop of the walk animation
constexpr double kCycleDistance = 0.32;

constexpr double kFleeDistance = 0.8;
constexpr double kSafeDistance = 1.6;
// Robot center this close to a paint can means it bumped into it
constexpr double kBumpDistance = 0.3;

constexpr double kPuddleWidth = 0.18;
constexpr int kDirtyPrints = 60;
constexpr double kPaintChance = 0.9;
// The cat stops making a mess while this many of its prints are left
constexpr int kMaxMess = 400;

// Strolls go to the cleanest of a few random spots nearby
constexpr int kGoalCandidates = 10;
constexpr double kStrollMin = 1.5;
constexpr double kStrollMax = 5.0;
constexpr double kCleanChance = 0.65;
constexpr double kMessyCleanChance = 0.95;

// Cats step the hind paw where the front one was so prints form one zigzag
constexpr double kPrintStep = 0.13;
constexpr double kPrintSide = 0.04;
constexpr double kPrintSize = 0.065;

double Wrap(double _a)
{
  return std::atan2(std::sin(_a), std::cos(_a));
}

int64_t ChunkKey(int _i, int _j)
{
  return (static_cast<int64_t>(_i) << 32) ^ static_cast<uint32_t>(_j);
}
}  // namespace

// Cat actor that walks paint all over the house for vacuum_dirt to clean.
// It steps in the puddle of a paint can and then heads for the cleanest
// floor leaving colored paw prints. It runs away from the vacuum robot and
// a can the robot bumps into disappears with its color.
// The walkable area comes from a PGM map where dark pixels are free.
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
    densityTopic =
      _sdf->Get<std::string>("density_topic", densityTopic).first;
    maxMess = _sdf->Get<int>("max_mess", kMaxMess).first;

    auto e = _sdf->FindElement("paint");
    for (; e; e = e->GetNextElement("paint"))
    {
      Paint p;
      p.model = e->Get<std::string>("model");
      p.spot = e->Get<math::Vector2d>("spot");
      p.color = e->Get<int>("color");
      paints.push_back(p);
    }

    // Without a start pose every run begins somewhere else
    randomStart = !_sdf->HasElement("start");
    auto start = _sdf->Get<math::Vector3d>("start");
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
    node.Subscribe(densityTopic, &CatWalker::OnDensity, this);
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
    CheckBumps(_ecm);
    Think(now);
    Move(dt);
    Apply(dt, _ecm);
    PublishDirt();
  }

private:
  enum class State { Idle, Walk, Flee };

  struct Paint
  {
    std::string model;
    Vector2d spot;
    int color{0};
    Entity can{kNullEntity};
    Vector2d canPos;
    bool active{true};
  };

  // Paw prints still on the floor according to the vacuum_dirt score
  void OnScore(const msgs::StringMsg &_msg)
  {
    const std::string &json = _msg.data();
    auto at = json.find("\"paw\":{");
    if (at == std::string::npos)
    {
      messLeft = 0;
      return;
    }
    auto total = json.find("\"total\":", at);
    auto collected = json.find("\"collected\":", at);
    if (total != std::string::npos && collected != std::string::npos)
      messLeft = std::atoi(json.c_str() + total + 8) -
        std::atoi(json.c_str() + collected + 12);
  }

  // Pieces left in every floor chunk
  void OnDensity(const msgs::StringMsg &_msg)
  {
    std::unordered_map<int64_t, int> counts;
    std::istringstream ss(_msg.data());
    std::string item;
    std::getline(ss, item, ';');
    double size = std::atof(item.c_str());
    while (std::getline(ss, item, ';'))
    {
      int i, j, n;
      if (std::sscanf(item.c_str(), "%d,%d,%d", &i, &j, &n) == 3)
        counts[ChunkKey(i, j)] = n;
    }
    std::lock_guard<std::mutex> lock(densityMutex);
    chunkSize = size;
    density.swap(counts);
  }

  int DirtAt(const Vector2d &_p)
  {
    std::lock_guard<std::mutex> lock(densityMutex);
    if (chunkSize <= 0.0)
      return 0;
    auto it = density.find(ChunkKey(
      static_cast<int>(std::floor(_p.X() / chunkSize)),
      static_cast<int>(std::floor(_p.Y() / chunkSize))));
    return it == density.end() ? 0 : it->second;
  }

  bool Tidy() const
  {
    return messLeft >= maxMess;
  }

  void Restart()
  {
    rng.seed(std::random_device{}());
    pos = startPos;
    yaw = startYaw;
    if (randomStart)
    {
      std::uniform_int_distribution<size_t> pick(0, freeCells.size() - 1);
      std::uniform_real_distribution<double> angle(-M_PI, M_PI);
      pos = Center(freeCells[pick(rng)]);
      yaw = angle(rng);
    }
    path.clear();
    state = State::Idle;
    stateUntil = 0.0;
    retryAt = 0.0;
    lastTime = 0.0;
    animTime = 0.0;
    dirtyPrints = 0;
    sinceLastPrint = 0.0;
    leftPaw = false;
    dirt.Clear();
    animation.clear();
    robot = kNullEntity;
    for (auto &p : paints)
    {
      p.can = kNullEntity;
      p.active = true;
    }
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

  // Usually the cleanest of a few random spots nearby
  Vector2d StrollGoal()
  {
    double away = robot != kNullEntity ? kSafeDistance : 0.0;
    std::uniform_real_distribution<double> u(0, 1);
    double clean = dirtyPrints > 0 ? kMessyCleanChance : kCleanChance;
    if (u(rng) >= clean)
      return RandomSpot(kStrollMin, kStrollMax, robotPos, away);

    Vector2d best;
    int bestDirt = -1;
    for (int k = 0; k < kGoalCandidates; ++k)
    {
      Vector2d p = RandomSpot(kStrollMin, kStrollMax, robotPos, away);
      int dirtHere = DirtAt(p);
      if (bestDirt < 0 || dirtHere < bestDirt)
      {
        best = p;
        bestDirt = dirtHere;
      }
    }
    return best;
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

  // A can the robot runs into is removed and its color is gone
  void CheckBumps(EntityComponentManager &_ecm)
  {
    for (auto &p : paints)
    {
      if (!p.active)
        continue;
      if (p.can == kNullEntity || !_ecm.HasEntity(p.can))
      {
        p.can = _ecm.EntityByComponents(components::Model(),
          components::Name(p.model));
        if (p.can == kNullEntity)
          continue;
      }
      auto c = worldPose(p.can, _ecm).Pos();
      p.canPos = Vector2d(c.X(), c.Y());
      if (robot == kNullEntity || robotPos.Distance(p.canPos) > kBumpDistance)
        continue;

      _ecm.RequestRemoveEntity(p.can);
      p.can = kNullEntity;
      p.active = false;
      if (printColor == p.color)
        dirtyPrints = 0;
    }
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
      std::vector<const Paint *> active;
      for (const auto &p : paints)
        if (p.active)
          active.push_back(&p);

      std::uniform_real_distribution<double> u(0, 1);
      Vector2d goal;
      if (!Tidy() && dirtyPrints == 0 && !active.empty() &&
          u(rng) < kPaintChance)
      {
        std::uniform_int_distribution<size_t> pick(0, active.size() - 1);
        goal = active[pick(rng)]->spot;
      }
      else
      {
        goal = StrollGoal();
      }

      if (Plan(goal))
        state = State::Walk;
      else
        retryAt = _now + 0.5;
    }

    if (state != State::Idle && path.empty())
    {
      std::uniform_real_distribution<double> rest(kRestMin, kRestMax);
      state = State::Idle;
      stateUntil = _now + rest(rng);
    }
  }

  void Move(double _dt)
  {
    for (const auto &p : paints)
    {
      if (p.active && OnPuddle(p))
      {
        dirtyPrints = kDirtyPrints;
        printColor = p.color;
      }
    }

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

    if (dirtyPrints > 0 && !Tidy())
    {
      sinceLastPrint += step;
      if (sinceLastPrint >= kPrintStep)
      {
        sinceLastPrint = 0.0;
        leftPaw = !leftPaw;
        double side = leftPaw ? kPrintSide : -kPrintSide;
        Vector2d at = pos + Vector2d(-std::sin(yaw), std::cos(yaw)) * side;
        std::ostringstream name;
        name << "paw paw " << kPrintSize << " " << kPrintSize << " "
             << printColor + (leftPaw ? 1 : 0);
        auto *p = dirt.add_pose();
        p->set_name(name.str());
        msgs::Set(p, Pose3d(at.X(), at.Y(), 0, 0, 0, yaw));
        --dirtyPrints;
      }
    }
  }

  // The puddle runs from the can to a bit past its spot
  bool OnPuddle(const Paint &_p) const
  {
    Vector2d a = _p.canPos;
    Vector2d ab = _p.spot - a;
    double t = std::clamp((pos - a).Dot(ab) / ab.SquaredLength(), 0.0, 1.15);
    return pos.Distance(a + ab * t) < kPuddleWidth;
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

  // The exported animations loop over 40 frames at 24 fps
  static constexpr double kCycleLength{40.0 / 24.0};

  std::string actorName{"cat"};
  std::string robotName{"vacuum_cleaner"};
  std::string dirtTopic{"/vacuum_dirt/add"};
  std::string scoreTopic{"/vacuum_dirt/score"};
  std::string densityTopic{"/vacuum_dirt/density"};
  int maxMess{kMaxMess};
  std::atomic<int> messLeft{0};
  std::vector<Paint> paints;
  bool randomStart{true};
  Vector2d startPos;
  double startYaw{0.0};

  int width{0};
  int height{0};
  double res{0.05};
  double ox{0.0};
  double oy{0.0};
  std::vector<bool> walkable;
  std::vector<int> freeCells;

  std::mutex densityMutex;
  std::unordered_map<int64_t, int> density;
  double chunkSize{0.0};

  Entity actor{kNullEntity};
  Entity robot{kNullEntity};
  Vector2d robotPos{1e6, 1e6};

  State state{State::Idle};
  double stateUntil{0.0};
  // A failed plan waits a bit because A* is too costly to retry every step
  double retryAt{0.0};
  double lastTime{0.0};
  Vector2d pos;
  double yaw{0.0};
  double speed{0.0};
  double animTime{0.0};
  std::string animation;
  std::vector<Vector2d> path;

  int dirtyPrints{0};
  int printColor{0};
  double sinceLastPrint{0.0};
  bool leftPaw{false};
  msgs::Pose_V dirt;

  std::mt19937 rng;
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
