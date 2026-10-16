#include <gz/sim/System.hh>
#include <gz/sim/Actor.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/Actor.hh>
#include <gz/sim/components/AngularVelocityCmd.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/plugin/Register.hh>
#include <gz/math/Pose3.hh>
#include <gz/math/Vector2.hh>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <queue>
#include <random>
#include <sstream>
#include <string>
#include <vector>

// Workers that carry boxes to random free spots and stroll around in between
// Each worker is an actor plus an invisible cylinder the robot can collide with

namespace warehouse_workers
{
using gz::math::Pose3d;
using gz::math::Vector2d;
using gz::math::Vector3d;
using gz::sim::Entity;
using gz::sim::EntityComponentManager;
using gz::sim::kNullEntity;

namespace
{
constexpr double kPersonRadius = 0.3;
constexpr double kBoxRadius = 0.3;
constexpr double kRobotRadius = 0.4;
// Distance from the worker to the box center while picking and placing
constexpr double kStandoff = 0.55;
// Must match the hand target of the carry animations
constexpr double kCarryAhead = 0.35;
constexpr double kCarryZ = 0.98;
constexpr double kLiftTime = 1.0;
constexpr double kTurnRate = 2.5;
constexpr double kTurnInPlace = 0.6;

double wrap(double a)
{
  return std::atan2(std::sin(a), std::cos(a));
}

double lerp(double a, double b, double t)
{
  return a + (b - a) * t;
}

std::vector<double> numbers(const std::string &text)
{
  std::vector<double> out;
  std::stringstream ss(text);
  double v;
  while (ss >> v)
    out.push_back(v);
  return out;
}
}  // namespace

struct Circle
{
  Vector2d c;
  double r;
};

struct Box
{
  std::string name;
  Entity entity{kNullEntity};
  double halfHeight{0.14};
  int owner{-1};
};

struct Worker
{
  enum class State { Start, ToBox, Lift, ToDrop, Lower, Stroll, Idle };

  std::string actorName;
  std::string bodyName;
  Entity actor{kNullEntity};
  Entity body{kNullEntity};
  Vector2d startPos;
  double startYaw{0.0};

  Vector2d pos;
  double yaw{0.0};
  double speed{0.0};
  State state{State::Start};
  std::vector<Vector2d> path;
  size_t wp{0};
  // Heading to face once the path ends
  bool faceTarget{false};
  Vector2d faceAt;
  double timer{0.0};
  double retryAt{0.0};
  double blockedTime{0.0};
  // After a detour the worker stops waiting for the others for a while
  double ignoreOthersUntil{0.0};
  int box{-1};
  int lastBox{-1};
  Vector2d dropAt;
  int strollsLeft{0};
  double animTime{0.0};
  bool moving{false};
  std::string animation;
  // Last pose sent to the actor so a still worker costs nothing
  bool shown{false};
  Vector2d shownPos;
  double shownYaw{0.0};
  double shownAnimTime{0.0};
  double shownSpeed{0.0};
};

class WarehouseWorkers :
    public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate,
    public gz::sim::ISystemReset
{
public:
  void Configure(const Entity &, const std::shared_ptr<const sdf::Element> &_sdf,
                 EntityComponentManager &, gz::sim::EventManager &) override
  {
    auto sdf = std::const_pointer_cast<sdf::Element>(_sdf);

    this->walkSpeed = sdf->Get<double>("walk_speed", 0.7).first;
    this->animPerMeter = sdf->Get<double>("animation_per_meter", 4.15).first;
    this->actorZ = sdf->Get<double>("actor_z", 1.0).first;
    this->robotName = sdf->Get<std::string>("robot", "").first;
    this->clearance = sdf->Get<double>("drop_clearance", 0.8).first;
    this->debug = sdf->Get<bool>("debug", false).first;

    if (sdf->HasElement("seed"))
      this->rng.seed(sdf->Get<unsigned int>("seed"));
    else
      this->rng.seed(std::random_device{}());

    for (auto e = sdf->FindElement("worker"); e; e = e->GetNextElement("worker"))
    {
      Worker w;
      w.actorName = e->Get<std::string>("actor");
      w.bodyName = e->Get<std::string>("body");
      auto p = numbers(e->Get<std::string>("start"));
      if (p.size() == 3)
      {
        w.startPos.Set(p[0], p[1]);
        w.startYaw = p[2];
      }
      this->workers.push_back(w);
    }
    for (auto e = sdf->FindElement("box"); e; e = e->GetNextElement("box"))
    {
      Box b;
      b.name = e->Get<std::string>();
      b.halfHeight = e->Get<double>("half_height", 0.14).first;
      this->boxes.push_back(b);
    }
    for (auto e = sdf->FindElement("keepout"); e; e = e->GetNextElement("keepout"))
    {
      auto v = numbers(e->Get<std::string>());
      if (v.size() == 3)
        this->keepouts.push_back({Vector2d(v[0], v[1]), v[2]});
    }

    if (!this->LoadMap(sdf->Get<std::string>("map"),
                       sdf->Get<double>("resolution", 0.05).first,
                       sdf->Get<double>("origin_x", 0.0).first,
                       sdf->Get<double>("origin_y", 0.0).first))
    {
      std::cerr << "[WarehouseWorkers] could not load the map, workers stay still\n";
      return;
    }
    this->ready = true;
  }

  void Reset(const gz::sim::UpdateInfo &, EntityComponentManager &_ecm) override
  {
    for (auto &w : this->workers)
    {
      w.state = Worker::State::Start;
      w.box = -1;
      w.lastBox = -1;
      w.path.clear();
      w.ignoreOthersUntil = 0.0;
      w.shown = false;
      w.animation.clear();
    }
    for (auto &b : this->boxes)
    {
      b.owner = -1;
      if (b.entity != kNullEntity)
        this->ReleaseModel(b.entity, _ecm);
    }
    this->lastSimTime = 0.0;
    this->robotLookupAt = 0.0;
    this->firstUpdate = true;
  }

  void PreUpdate(const gz::sim::UpdateInfo &_info, EntityComponentManager &_ecm) override
  {
    if (!this->ready)
      return;
    if (!this->FindEntities(_ecm))
      return;

    double now = std::chrono::duration<double>(_info.simTime).count();
    if (now < this->lastSimTime)
      this->Reset(_info, _ecm);
    double dt = now - this->lastSimTime;
    this->lastSimTime = now;
    this->now = now;

    if (this->firstUpdate)
    {
      this->Scatter(_ecm);
      this->firstUpdate = false;
    }

    if (_info.paused)
      return;
    dt = std::clamp(dt, 0.0, 0.05);

    for (size_t i = 0; i < this->workers.size(); ++i)
      this->Step(static_cast<int>(i), dt, _ecm);
  }

private:
  bool LoadMap(const std::string &file, double res, double ox, double oy)
  {
    std::ifstream in(file, std::ios::binary);
    if (!in)
      return false;
    std::string magic;
    int maxval;
    in >> magic;
    // Skip comment lines of the header
    auto next = [&in]() {
      in >> std::ws;
      while (in.peek() == '#')
      {
        std::string line;
        std::getline(in, line);
        in >> std::ws;
      }
    };
    next();
    in >> this->width;
    next();
    in >> this->height;
    next();
    in >> maxval;
    in.get();
    if (magic != "P5" || this->width <= 0 || this->height <= 0)
      return false;
    std::vector<unsigned char> raw(this->width * this->height);
    in.read(reinterpret_cast<char *>(raw.data()), raw.size());

    this->res = res;
    this->ox = ox;
    this->oy = oy;
    // White cells are occupied and the first row is the top of the map
    this->occupied.assign(raw.size(), false);
    for (int r = 0; r < this->height; ++r)
      for (int c = 0; c < this->width; ++c)
        this->occupied[this->Index(c, this->height - 1 - r)] = raw[r * this->width + c] > 127;

    // Distance to the closest obstacle in meters by a two pass chamfer
    const double inf = 1e9;
    this->dist.assign(raw.size(), inf);
    for (size_t i = 0; i < raw.size(); ++i)
      if (this->occupied[i])
        this->dist[i] = 0.0;
    const double d1 = res, d2 = res * std::sqrt(2.0);
    for (int y = 0; y < this->height; ++y)
      for (int x = 0; x < this->width; ++x)
      {
        double &d = this->dist[this->Index(x, y)];
        if (x > 0) d = std::min(d, this->dist[this->Index(x - 1, y)] + d1);
        if (y > 0) d = std::min(d, this->dist[this->Index(x, y - 1)] + d1);
        if (x > 0 && y > 0) d = std::min(d, this->dist[this->Index(x - 1, y - 1)] + d2);
        if (x < this->width - 1 && y > 0) d = std::min(d, this->dist[this->Index(x + 1, y - 1)] + d2);
      }
    for (int y = this->height - 1; y >= 0; --y)
      for (int x = this->width - 1; x >= 0; --x)
      {
        double &d = this->dist[this->Index(x, y)];
        if (x < this->width - 1) d = std::min(d, this->dist[this->Index(x + 1, y)] + d1);
        if (y < this->height - 1) d = std::min(d, this->dist[this->Index(x, y + 1)] + d1);
        if (x < this->width - 1 && y < this->height - 1) d = std::min(d, this->dist[this->Index(x + 1, y + 1)] + d2);
        if (x > 0 && y < this->height - 1) d = std::min(d, this->dist[this->Index(x - 1, y + 1)] + d2);
      }
    return true;
  }

  int Index(int x, int y) const { return y * this->width + x; }

  bool Cell(const Vector2d &p, int &x, int &y) const
  {
    x = static_cast<int>(std::floor((p.X() - this->ox) / this->res));
    y = static_cast<int>(std::floor((p.Y() - this->oy) / this->res));
    return x >= 0 && y >= 0 && x < this->width && y < this->height;
  }

  Vector2d Center(int x, int y) const
  {
    return Vector2d(this->ox + (x + 0.5) * this->res, this->oy + (y + 0.5) * this->res);
  }

  double WallDistance(const Vector2d &p) const
  {
    int x, y;
    if (!this->Cell(p, x, y))
      return 0.0;
    return this->dist[this->Index(x, y)];
  }

  bool FindEntities(EntityComponentManager &_ecm)
  {
    if (this->found)
      return true;
    for (auto &w : this->workers)
    {
      w.actor = _ecm.EntityByComponents(gz::sim::components::Name(w.actorName));
      w.body = _ecm.EntityByComponents(gz::sim::components::Name(w.bodyName),
                                       gz::sim::components::Model());
      if (w.actor == kNullEntity || w.body == kNullEntity)
        return false;
    }
    for (auto &b : this->boxes)
    {
      b.entity = _ecm.EntityByComponents(gz::sim::components::Name(b.name),
                                         gz::sim::components::Model());
      if (b.entity == kNullEntity)
        return false;
    }
    this->found = true;
    return true;
  }

  Vector2d BoxPos(const Box &b, EntityComponentManager &_ecm) const
  {
    auto p = gz::sim::worldPose(b.entity, _ecm);
    return Vector2d(p.Pos().X(), p.Pos().Y());
  }

  bool RobotPos(EntityComponentManager &_ecm, Vector2d &out)
  {
    if (this->robotName.empty())
      return false;
    // The robot is spawned after the world so it is looked up until found
    if (this->robot == kNullEntity || !_ecm.HasEntity(this->robot))
    {
      if (this->now < this->robotLookupAt)
        return false;
      this->robotLookupAt = this->now + 1.0;
      this->robot = _ecm.EntityByComponents(gz::sim::components::Name(this->robotName),
                                            gz::sim::components::Model());
      if (this->robot == kNullEntity)
        return false;
    }
    auto p = gz::sim::worldPose(this->robot, _ecm);
    out.Set(p.Pos().X(), p.Pos().Y());
    return true;
  }

  void SetModelPose(Entity e, const Pose3d &pose, const Vector3d &vel,
                    EntityComponentManager &_ecm)
  {
    gz::sim::Model(e).SetWorldPoseCmd(_ecm, pose);
    // Body frame velocity so contacts see a moving object and gravity
    // never builds up while the pose is being set
    auto lin = _ecm.Component<gz::sim::components::LinearVelocityCmd>(e);
    if (lin)
      *lin = gz::sim::components::LinearVelocityCmd(vel);
    else
      _ecm.CreateComponent(e, gz::sim::components::LinearVelocityCmd(vel));
    auto ang = _ecm.Component<gz::sim::components::AngularVelocityCmd>(e);
    if (ang)
      *ang = gz::sim::components::AngularVelocityCmd(Vector3d::Zero);
    else
      _ecm.CreateComponent(e, gz::sim::components::AngularVelocityCmd(Vector3d::Zero));
  }

  void ReleaseModel(Entity e, EntityComponentManager &_ecm)
  {
    _ecm.RemoveComponent<gz::sim::components::LinearVelocityCmd>(e);
    _ecm.RemoveComponent<gz::sim::components::AngularVelocityCmd>(e);
  }

  // Random free spot away from walls and keepouts and the robot and the other boxes
  bool RandomSpot(Vector2d &out, int ignoreBox, EntityComponentManager &_ecm,
                  const std::vector<Vector2d> &taken = {})
  {
    std::vector<Circle> avoid = this->keepouts;
    Vector2d robot;
    if (this->RobotPos(_ecm, robot))
      avoid.push_back({robot, 1.2});
    for (size_t i = 0; i < this->boxes.size(); ++i)
      if (static_cast<int>(i) != ignoreBox)
        avoid.push_back({this->BoxPos(this->boxes[i], _ecm), 1.2});
    for (const auto &t : taken)
      avoid.push_back({t, 1.2});
    for (const auto &w : this->workers)
      avoid.push_back({w.pos, 1.0});

    std::uniform_real_distribution<double> ux(this->ox, this->ox + this->width * this->res);
    std::uniform_real_distribution<double> uy(this->oy, this->oy + this->height * this->res);
    for (int i = 0; i < 2000; ++i)
    {
      Vector2d p(ux(this->rng), uy(this->rng));
      if (this->WallDistance(p) < this->clearance)
        continue;
      bool free = true;
      for (const auto &a : avoid)
        free = free && p.Distance(a.c) >= a.r;
      if (free)
      {
        out = p;
        return true;
      }
    }
    return false;
  }

  void Scatter(EntityComponentManager &_ecm)
  {
    for (auto &w : this->workers)
    {
      w.pos = w.startPos;
      w.yaw = w.startYaw;
    }
    std::vector<Vector2d> taken;
    std::uniform_real_distribution<double> uyaw(-M_PI, M_PI);
    for (size_t i = 0; i < this->boxes.size(); ++i)
    {
      Vector2d p;
      if (!this->RandomSpot(p, static_cast<int>(i), _ecm, taken))
        continue;
      taken.push_back(p);
      Pose3d pose(p.X(), p.Y(), this->boxes[i].halfHeight, 0, 0, uyaw(this->rng));
      gz::sim::Model(this->boxes[i].entity).SetWorldPoseCmd(_ecm, pose);
    }
  }

  // Cells a worker may step on while boxes and the robot block their surroundings
  std::vector<bool> Walkable(int self, int targetBox, EntityComponentManager &_ecm)
  {
    std::vector<bool> ok(this->occupied.size());
    for (size_t i = 0; i < ok.size(); ++i)
      ok[i] = this->dist[i] > kPersonRadius;

    std::vector<Circle> blocks;
    for (size_t i = 0; i < this->boxes.size(); ++i)
    {
      const auto &b = this->boxes[i];
      if (static_cast<int>(i) == targetBox || b.owner >= 0)
        continue;
      blocks.push_back({this->BoxPos(b, _ecm), kBoxRadius + kPersonRadius});
    }
    Vector2d robot;
    if (this->RobotPos(_ecm, robot))
      blocks.push_back({robot, kRobotRadius + kPersonRadius});
    for (size_t i = 0; i < this->workers.size(); ++i)
      if (static_cast<int>(i) != self)
        blocks.push_back({this->workers[i].pos, 2 * kPersonRadius});

    const Vector2d &me = this->workers[self].pos;
    for (auto b : blocks)
    {
      // A worker standing next to a box must still be able to walk away
      b.r = std::min(b.r, b.c.Distance(me) - 2 * this->res);
      if (b.r <= 0.0)
        continue;
      int cx, cy;
      this->Cell(b.c, cx, cy);
      int n = static_cast<int>(std::ceil(b.r / this->res));
      for (int y = cy - n; y <= cy + n; ++y)
        for (int x = cx - n; x <= cx + n; ++x)
          if (x >= 0 && y >= 0 && x < this->width && y < this->height &&
              this->Center(x, y).Distance(b.c) < b.r)
            ok[this->Index(x, y)] = false;
    }
    return ok;
  }

  bool LineFree(const Vector2d &a, const Vector2d &b, const std::vector<bool> &ok) const
  {
    double len = a.Distance(b);
    int steps = std::max(1, static_cast<int>(len / (this->res * 0.5)));
    for (int i = 0; i <= steps; ++i)
    {
      Vector2d p = a + (b - a) * (static_cast<double>(i) / steps);
      int x, y;
      if (!this->Cell(p, x, y) || !ok[this->Index(x, y)])
        return false;
    }
    return true;
  }

  // A* over the grid followed by line of sight shortcuts
  bool Plan(const Vector2d &from, const Vector2d &to, const std::vector<bool> &ok,
            std::vector<Vector2d> &path) const
  {
    int sx, sy, gx, gy;
    if (!this->Cell(from, sx, sy) || !this->Cell(to, gx, gy))
      return false;
    int goal = this->Index(gx, gy);
    if (!ok[goal])
      return false;

    const int n = this->width * this->height;
    std::vector<double> g(n, 1e18);
    std::vector<int> parent(n, -1);
    std::vector<bool> closed(n, false);
    using Item = std::pair<double, int>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> open;
    int start = this->Index(sx, sy);
    g[start] = 0.0;
    auto h = [&](int x, int y) {
      double dx = std::abs(x - gx), dy = std::abs(y - gy);
      return std::max(dx, dy) + (std::sqrt(2.0) - 1.0) * std::min(dx, dy);
    };
    open.push({h(sx, sy), start});
    bool reached = false;
    while (!open.empty())
    {
      int cur = open.top().second;
      open.pop();
      if (closed[cur])
        continue;
      closed[cur] = true;
      if (cur == goal)
      {
        reached = true;
        break;
      }
      int cx = cur % this->width, cy = cur / this->width;
      for (int dy = -1; dy <= 1; ++dy)
        for (int dx = -1; dx <= 1; ++dx)
        {
          if (!dx && !dy)
            continue;
          int x = cx + dx, y = cy + dy;
          if (x < 0 || y < 0 || x >= this->width || y >= this->height)
            continue;
          int ni = this->Index(x, y);
          if (!ok[ni] || closed[ni])
            continue;
          double step = (dx && dy) ? std::sqrt(2.0) : 1.0;
          if (g[cur] + step < g[ni])
          {
            g[ni] = g[cur] + step;
            parent[ni] = cur;
            open.push({g[ni] + h(x, y), ni});
          }
        }
    }
    if (!reached)
      return false;

    std::vector<Vector2d> cells;
    for (int c = goal; c != -1; c = parent[c])
      cells.push_back(this->Center(c % this->width, c / this->width));
    std::reverse(cells.begin(), cells.end());
    cells.front() = from;
    cells.back() = to;

    path.clear();
    size_t i = 0;
    while (i + 1 < cells.size())
    {
      size_t j = cells.size() - 1;
      while (j > i + 1 && !this->LineFree(cells[i], cells[j], ok))
        --j;
      path.push_back(cells[j]);
      i = j;
    }
    return !path.empty();
  }

  // Closest walkable spot at kStandoff from a target
  bool Approach(const Worker &w, const Vector2d &target, const std::vector<bool> &ok,
                Vector2d &out) const
  {
    double best = 1e18;
    bool found = false;
    for (int k = 0; k < 16; ++k)
    {
      double a = k * M_PI / 8.0;
      Vector2d p = target + Vector2d(std::cos(a), std::sin(a)) * kStandoff;
      int x, y;
      if (!this->Cell(p, x, y) || !ok[this->Index(x, y)])
        continue;
      double d = p.Distance(w.pos);
      if (d < best)
      {
        best = d;
        out = p;
        found = true;
      }
    }
    return found;
  }

  bool GoTo(int i, const Vector2d &goal, bool face, const Vector2d &faceAt,
            int targetBox, EntityComponentManager &_ecm)
  {
    auto &w = this->workers[i];
    auto ok = this->Walkable(i, targetBox, _ecm);
    std::vector<Vector2d> path;
    if (!this->Plan(w.pos, goal, ok, path))
      return false;
    w.path = path;
    w.wp = 0;
    w.faceTarget = face;
    w.faceAt = faceAt;
    w.blockedTime = 0.0;
    return true;
  }

  // Plans around the other workers and stops waiting for them for a while
  bool Detour(int i, int targetBox, EntityComponentManager &_ecm)
  {
    auto &w = this->workers[i];
    w.blockedTime = 0.0;
    w.ignoreOthersUntil = this->now + 4.0;
    return this->GoTo(i, w.path.back(), w.faceTarget, w.faceAt, targetBox, _ecm);
  }

  bool PickBox(int i, EntityComponentManager &_ecm)
  {
    auto &w = this->workers[i];
    std::vector<int> options;
    for (size_t b = 0; b < this->boxes.size(); ++b)
      if (this->boxes[b].owner < 0 && static_cast<int>(b) != w.lastBox)
        options.push_back(static_cast<int>(b));
    std::shuffle(options.begin(), options.end(), this->rng);
    for (int b : options)
    {
      Vector2d boxPos = this->BoxPos(this->boxes[b], _ecm);
      auto ok = this->Walkable(i, b, _ecm);
      Vector2d stand;
      if (!this->Approach(w, boxPos, ok, stand))
      {
        this->Log(i, "no approach to " + this->boxes[b].name);
        continue;
      }
      if (!this->GoTo(i, stand, true, boxPos, b, _ecm))
      {
        this->Log(i, "no path to " + this->boxes[b].name);
        continue;
      }
      this->boxes[b].owner = i;
      w.box = b;
      w.state = Worker::State::ToBox;
      return true;
    }
    return false;
  }

  bool PickDrop(int i, EntityComponentManager &_ecm)
  {
    auto &w = this->workers[i];
    auto ok = this->Walkable(i, -1, _ecm);
    for (int tries = 0; tries < 20; ++tries)
    {
      Vector2d drop;
      if (!this->RandomSpot(drop, w.box, _ecm))
        return false;
      if (drop.Distance(w.pos) < 3.0)
        continue;
      Vector2d stand;
      if (!this->Approach(w, drop, ok, stand))
        continue;
      if (!this->GoTo(i, stand, true, drop, -1, _ecm))
        continue;
      w.dropAt = drop;
      w.state = Worker::State::ToDrop;
      return true;
    }
    return false;
  }

  bool PickStroll(int i, EntityComponentManager &_ecm)
  {
    auto &w = this->workers[i];
    for (int tries = 0; tries < 20; ++tries)
    {
      Vector2d p;
      if (!this->RandomSpot(p, -1, _ecm))
        return false;
      if (p.Distance(w.pos) < 2.0)
        continue;
      if (this->GoTo(i, p, false, p, -1, _ecm))
      {
        w.state = Worker::State::Stroll;
        return true;
      }
    }
    return false;
  }

  void Idle(Worker &w, double minTime, double maxTime)
  {
    std::uniform_real_distribution<double> u(minTime, maxTime);
    w.timer = u(this->rng);
    w.state = Worker::State::Idle;
    w.path.clear();
  }

  // Follows the path and returns true once the final turn is done
  bool Walk(int i, double dt)
  {
    auto &w = this->workers[i];
    w.speed = 0.0;
    w.moving = false;
    if (w.wp < w.path.size())
    {
      // Wait while another worker stands right ahead
      Vector2d ahead = w.path[w.wp] - w.pos;
      ahead.Normalize();
      for (size_t j = 0; j < this->workers.size() && this->now >= w.ignoreOthersUntil; ++j)
      {
        Vector2d d = this->workers[j].pos - w.pos;
        if (static_cast<int>(j) != i && d.Length() < 0.9 && d.Dot(ahead) > 0.5 * d.Length())
        {
          w.blockedTime += dt;
          return false;
        }
      }
      w.blockedTime = 0.0;

      Vector2d target = w.path[w.wp];
      Vector2d d = target - w.pos;
      double dist = d.Length();
      double err = wrap(std::atan2(d.Y(), d.X()) - w.yaw);
      double turn = std::clamp(err, -kTurnRate * dt, kTurnRate * dt);
      w.yaw = wrap(w.yaw + turn);
      w.animTime += std::abs(turn) * 0.3;
      w.moving = w.moving || std::abs(turn) > 1e-4;
      if (std::abs(err) < kTurnInPlace)
      {
        double step = std::min(dist, this->walkSpeed * dt);
        w.pos += Vector2d(std::cos(w.yaw), std::sin(w.yaw)) * step;
        w.speed = step / std::max(dt, 1e-6);
        w.animTime += step * this->animPerMeter;
        w.moving = true;
      }
      if (w.pos.Distance(target) < 0.03)
      {
        w.pos = target;
        ++w.wp;
      }
      return false;
    }
    if (w.faceTarget)
    {
      Vector2d d = w.faceAt - w.pos;
      double err = wrap(std::atan2(d.Y(), d.X()) - w.yaw);
      double turn = std::clamp(err, -kTurnRate * dt, kTurnRate * dt);
      w.yaw = wrap(w.yaw + turn);
      w.animTime += std::abs(turn) * 0.3;
      w.moving = w.moving || std::abs(turn) > 1e-4;
      if (std::abs(err) > 0.02)
        return false;
    }
    return true;
  }

  void Log(int i, const std::string &msg) const
  {
    if (this->debug)
      std::cout << "[WarehouseWorkers] t=" << this->now << " " << this->workers[i].actorName
                << " " << msg << std::endl;
  }

  void Step(int i, double dt, EntityComponentManager &_ecm)
  {
    auto &w = this->workers[i];
    auto before = w.state;
    std::uniform_int_distribution<int> strolls(1, 2);

    switch (w.state)
    {
      case Worker::State::Start:
        w.pos = w.startPos;
        w.yaw = w.startYaw;
        this->Idle(w, 1.0, 4.0);
        break;

      case Worker::State::Idle:
        w.speed = 0.0;
        w.moving = false;
        w.timer -= dt;
        if (w.timer <= 0.0)
        {
          if (w.strollsLeft > 0)
          {
            --w.strollsLeft;
            if (!this->PickStroll(i, _ecm))
            {
              this->Log(i, "no stroll");
              this->Idle(w, 1.0, 2.0);
            }
          }
          else if (!this->PickBox(i, _ecm))
          {
            this->Log(i, "no box to pick");
            this->Idle(w, 1.0, 2.0);
          }
        }
        break;

      case Worker::State::ToBox:
        if (this->Walk(i, dt))
        {
          // The robot may have pushed the box since the worker set off
          w.faceAt = this->BoxPos(this->boxes[w.box], _ecm);
          w.state = Worker::State::Lift;
          w.timer = 0.0;
          w.retryAt = 0.0;
        }
        else if (w.blockedTime > 2.0 && !this->Detour(i, w.box, _ecm))
        {
          this->boxes[w.box].owner = -1;
          w.box = -1;
          this->Idle(w, 1.0, 2.0);
        }
        break;

      case Worker::State::Lift:
        w.moving = false;
        w.timer += dt;
        if (w.timer >= kLiftTime && w.timer >= w.retryAt)
        {
          if (!this->PickDrop(i, _ecm))
          {
            w.retryAt = w.timer + 0.5;
            this->Log(i, "no drop spot");
            // With nowhere to go the box goes back where it was
            if (w.timer > kLiftTime + 8.0)
            {
              w.dropAt = w.faceAt;
              w.state = Worker::State::Lower;
              w.timer = 0.0;
            }
          }
        }
        break;

      case Worker::State::ToDrop:
        if (this->Walk(i, dt))
        {
          w.state = Worker::State::Lower;
          w.timer = 0.0;
        }
        else if (w.blockedTime > 2.0)
        {
          this->Detour(i, -1, _ecm);
        }
        break;

      case Worker::State::Lower:
        w.moving = false;
        w.timer += dt;
        if (w.timer >= kLiftTime)
        {
          this->ReleaseModel(this->boxes[w.box].entity, _ecm);
          this->boxes[w.box].owner = -1;
          w.lastBox = w.box;
          w.box = -1;
          w.strollsLeft = strolls(this->rng);
          this->Idle(w, 0.5, 1.5);
        }
        break;

      case Worker::State::Stroll:
        if (this->Walk(i, dt))
          this->Idle(w, 2.0, 6.0);
        else if (w.blockedTime > 2.0 && !this->Detour(i, -1, _ecm))
          this->Idle(w, 0.5, 1.0);
        break;
    }

    if (w.state != before)
      this->Log(i, "state " + std::to_string(static_cast<int>(before)) + " -> " +
                       std::to_string(static_cast<int>(w.state)) + " box " + std::to_string(w.box));
    this->Apply(i, _ecm);
  }

  void Apply(int i, EntityComponentManager &_ecm)
  {
    auto &w = this->workers[i];
    gz::sim::Actor actor(w.actor);
    // Walking or standing with or without a box in the hands
    bool carrying = w.state == Worker::State::Lift || w.state == Worker::State::ToDrop ||
                    w.state == Worker::State::Lower;
    std::string animation = w.moving ? (carrying ? "carry" : "walk")
                                     : (carrying ? "stand_carry" : "stand");
    if (animation != w.animation || !actor.AnimationName(_ecm))
    {
      actor.SetAnimationName(_ecm, animation);
      _ecm.SetChanged(w.actor, gz::sim::components::AnimationName::typeId,
                      gz::sim::ComponentState::OneTimeChange);
      w.animation = animation;
    }
    bool still = w.pos == w.shownPos && w.yaw == w.shownYaw &&
                 w.animTime == w.shownAnimTime && w.speed == w.shownSpeed;
    Vector3d forward(w.speed, 0, 0);
    if (!still || !w.shown)
    {
      // The walk mesh stands upright and faces +x with its hips at actorZ
      Pose3d pose(w.pos.X(), w.pos.Y(), this->actorZ, 0.0, 0.0, w.yaw);
      actor.SetTrajectoryPose(_ecm, pose);
      actor.SetAnimationTime(_ecm, std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                                       std::chrono::duration<double>(w.animTime)));
      // The Actor setters do not flag the change so the GUI would never see it
      _ecm.SetChanged(w.actor, gz::sim::components::TrajectoryPose::typeId,
                      gz::sim::ComponentState::PeriodicChange);
      _ecm.SetChanged(w.actor, gz::sim::components::AnimationTime::typeId,
                      gz::sim::ComponentState::PeriodicChange);
      this->SetModelPose(w.body, Pose3d(w.pos.X(), w.pos.Y(), 0.0, 0, 0, w.yaw), forward, _ecm);
      w.shownPos = w.pos;
      w.shownYaw = w.yaw;
      w.shownAnimTime = w.animTime;
      w.shownSpeed = w.speed;
      w.shown = true;
    }

    if (w.box < 0 || this->boxes[w.box].owner != i)
      return;
    const auto &b = this->boxes[w.box];
    Vector2d ahead(std::cos(w.yaw), std::sin(w.yaw));
    double t = 1.0;
    Vector2d floorPos;
    if (w.state == Worker::State::Lift)
    {
      t = std::min(1.0, w.timer / kLiftTime);
      floorPos = w.faceAt;
    }
    else if (w.state == Worker::State::Lower)
    {
      t = 1.0 - std::min(1.0, w.timer / kLiftTime);
      floorPos = w.dropAt;
    }
    else if (w.state != Worker::State::ToDrop)
    {
      return;
    }
    Vector2d carry = w.pos + ahead * kCarryAhead;
    Vector2d xy = (w.state == Worker::State::ToDrop) ? carry : floorPos + (carry - floorPos) * t;
    double z = lerp(b.halfHeight, kCarryZ, t);
    this->SetModelPose(b.entity, Pose3d(xy.X(), xy.Y(), z, 0, 0, w.yaw),
                       w.state == Worker::State::ToDrop ? forward : Vector3d::Zero, _ecm);
  }

  bool ready{false};
  bool found{false};
  bool firstUpdate{true};
  double lastSimTime{0.0};
  double now{0.0};
  bool debug{false};

  double walkSpeed{0.7};
  double animPerMeter{4.15};
  double actorZ{1.0};
  double clearance{0.8};
  std::string robotName;
  Entity robot{kNullEntity};
  double robotLookupAt{0.0};

  std::vector<Worker> workers;
  std::vector<Box> boxes;
  std::vector<Circle> keepouts;
  std::mt19937 rng;

  int width{0};
  int height{0};
  double res{0.05};
  double ox{0.0};
  double oy{0.0};
  std::vector<bool> occupied;
  std::vector<double> dist;
};
}  // namespace warehouse_workers

GZ_ADD_PLUGIN(warehouse_workers::WarehouseWorkers,
              gz::sim::System,
              warehouse_workers::WarehouseWorkers::ISystemConfigure,
              warehouse_workers::WarehouseWorkers::ISystemPreUpdate,
              warehouse_workers::WarehouseWorkers::ISystemReset)

GZ_ADD_PLUGIN_ALIAS(warehouse_workers::WarehouseWorkers, "warehouse_workers::WarehouseWorkers")
