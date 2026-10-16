#include <unistd.h>

#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include <gz/common/Console.hh>
#include <gz/common/Util.hh>
#include <gz/sim/System.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/EventManager.hh>
#include <gz/sim/SdfEntityCreator.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/Pose.hh>

#include <gz/msgs/pose_v.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/msgs/Utility.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>

#include <sdf/Model.hh>
#include <sdf/Root.hh>

using namespace gz;
using namespace sim;

namespace vacuum_dirt
{

namespace fs = std::filesystem;

// Dirt colors by index. Confetti uses the first 24 and paints the rest
const std::vector<std::array<uint8_t, 3>> kPalette = []()
{
  const std::vector<std::array<double, 3>> base = {
    {0.85, 0.08, 0.15}, {0.96, 0.76, 0.10}, {0.10, 0.35, 0.88},
    {0.10, 0.68, 0.30}, {0.96, 0.42, 0.70}, {0.55, 0.22, 0.82},
    {0.95, 0.95, 0.95}, {0.98, 0.50, 0.08}};
  const double shades[] = {0.75, 0.9, 1.0};

  std::vector<std::array<uint8_t, 3>> p;
  for (const auto &c : base)
    for (double s : shades)
      p.push_back({static_cast<uint8_t>(c[0] * s * 255),
                   static_cast<uint8_t>(c[1] * s * 255),
                   static_cast<uint8_t>(c[2] * s * 255)});
  const std::vector<std::array<uint8_t, 3>> paints = {
    {204, 26, 26}, {170, 18, 18}, {26, 72, 210}, {18, 54, 176},
    {26, 158, 56}, {18, 128, 44}, {245, 204, 20}, {214, 172, 10},
    {140, 38, 192}, {112, 28, 160}, {255, 128, 12}, {222, 104, 8},
    {250, 90, 166}, {218, 66, 138}, {12, 190, 216}, {8, 156, 180}};
  p.insert(p.end(), paints.begin(), paints.end());
  return p;
}();
const int kAtlasCols = 8;
const int kAtlasRows = 5;
const int kCellPx = 8;

// Dirt on the floor that the vacuum robot sucks up as it drives over it.
// Pieces are merged into one mesh per floor chunk because thousands of
// separate visuals render far too slow. A chunk mesh is rewritten whenever
// the robot picks up one of its pieces.
// The pieces file has one piece per line as "category shape x y yaw size_x
// size_y color". Other plugins add dirt by publishing poses on <add_topic>
// named "category shape size_x size_y color".
class VacuumDirt:
  public System,
  public ISystemConfigure,
  public ISystemPreUpdate,
  public ISystemReset
{
public:
  ~VacuumDirt() override
  {
    std::error_code ec;
    fs::remove_all(meshDir, ec);
  }

  void Configure(
    const Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    EntityComponentManager &_ecm,
    EventManager &_eventMgr) override
  {
    world = _entity;
    creator = std::make_unique<SdfEntityCreator>(_ecm, _eventMgr);

    if (_sdf->HasElement("robot"))
      robotName = _sdf->Get<std::string>("robot");
    if (_sdf->HasElement("radius"))
      radius = _sdf->Get<double>("radius");
    if (_sdf->HasElement("floor_z"))
      floorZ = _sdf->Get<double>("floor_z");
    if (_sdf->HasElement("chunk_size"))
      chunkSize = _sdf->Get<double>("chunk_size");
    if (_sdf->HasElement("topic"))
      topic = _sdf->Get<std::string>("topic");
    if (_sdf->HasElement("density_topic"))
      densityTopic = _sdf->Get<std::string>("density_topic");
    if (_sdf->HasElement("add_topic"))
      addTopic = _sdf->Get<std::string>("add_topic");
    if (_sdf->HasElement("max_added"))
      maxAdded = _sdf->Get<int>("max_added");
    if (_sdf->HasElement("pieces"))
    {
      piecesFile = common::findFile(_sdf->Get<std::string>("pieces"));
      if (piecesFile.empty())
        gzerr << "vacuum_dirt: pieces file ["
              << _sdf->Get<std::string>("pieces") << "] not found\n";
    }

    meshDir = (fs::temp_directory_path() /
      ("vacuum_dirt_" + std::to_string(getpid()))).string();
    fs::create_directories(meshDir);
    WriteAtlas();

    scorePub = node.Advertise<msgs::StringMsg>(topic);
    densityPub = node.Advertise<msgs::StringMsg>(densityTopic);
    node.Subscribe(addTopic, &VacuumDirt::OnAdd, this);

    Populate(_ecm);
  }

  void PreUpdate(
    const UpdateInfo &_info,
    EntityComponentManager &_ecm) override
  {
    if (needsPopulate)
      Populate(_ecm);

    AddPending();

    if (!_info.paused)
      Clean(_ecm);

    // The world starts paused so the first meshes can't wait for sim time
    double t = std::chrono::duration<double>(_info.simTime).count();
    if (forceRebuild || t - lastRebuild >= kRebuildPeriod || t < lastRebuild)
    {
      forceRebuild = false;
      Rebuild(_ecm);
      lastRebuild = t;
    }

    auto now = std::chrono::steady_clock::now();
    auto since = now - lastPublish;
    if ((scoreChanged && since > std::chrono::milliseconds(200)) ||
        since > std::chrono::seconds(1))
      Publish(now);
  }

  void Reset(const UpdateInfo &, EntityComponentManager &) override
  {
    needsPopulate = true;
  }

private:
  struct Piece
  {
    std::string category;
    std::string shape;
    double x;
    double y;
    double z;
    double yaw;
    double sx;
    double sy;
    int color;
    // Added at runtime and limited by <max_added>
    bool runtime{false};
  };

  struct Chunk
  {
    std::vector<Piece> pieces;
    Entity model{kNullEntity};
    bool dirty{false};
  };

  struct Stats
  {
    int total{0};
    int collected{0};
  };

  static int64_t Key(int _i, int _j)
  {
    return (static_cast<int64_t>(_i) << 32) ^ static_cast<uint32_t>(_j);
  }

  int Cell(double _v) const
  {
    return static_cast<int>(std::floor(_v / chunkSize));
  }

  void Populate(EntityComponentManager &_ecm)
  {
    // Drop whatever a reset left behind and start again from the file
    _ecm.Each<components::Model, components::Name>(
      [&](const Entity &_model, const components::Model *,
          const components::Name *_name) -> bool
      {
        if (_name->Data().rfind(kChunkPrefix, 0) == 0)
          _ecm.RequestRemoveEntity(_model);
        return true;
      });
    chunks.clear();
    stats.clear();
    robot = kNullEntity;
    addedLeft = 0;
    {
      std::lock_guard<std::mutex> lock(pendingMutex);
      pending.clear();
    }

    std::ifstream in(piecesFile);
    std::string line;
    while (std::getline(in, line))
    {
      if (line.empty() || line[0] == '#')
        continue;
      std::istringstream ss(line);
      Piece p;
      ss >> p.category >> p.shape >> p.x >> p.y >> p.yaw >> p.sx >> p.sy
         >> p.color;
      if (!ss.fail())
        Add(p);
    }

    needsPopulate = false;
    forceRebuild = true;
    scoreChanged = true;
  }

  void Add(Piece _p)
  {
    // Tiny height jitter so overlapping pieces don't z-fight
    _p.z = floorZ + 0.0005 + 0.0008 * ((added++ * 7919) % 1000) / 1000.0;
    auto &chunk = chunks[Key(Cell(_p.x), Cell(_p.y))];
    chunk.pieces.push_back(_p);
    chunk.dirty = true;
    stats[_p.category].total++;
    scoreChanged = true;
  }

  void OnAdd(const msgs::Pose_V &_msg)
  {
    std::lock_guard<std::mutex> lock(pendingMutex);
    for (const auto &pose : _msg.pose())
    {
      Piece p;
      std::istringstream ss(pose.name());
      ss >> p.category >> p.shape >> p.sx >> p.sy >> p.color;
      if (ss.fail())
      {
        gzwarn << "vacuum_dirt: bad dirt [" << pose.name() << "]\n";
        continue;
      }
      p.x = pose.position().x();
      p.y = pose.position().y();
      p.yaw = msgs::Convert(pose.orientation()).Euler().Z();
      pending.push_back(p);
    }
  }

  void AddPending()
  {
    std::vector<Piece> added;
    {
      std::lock_guard<std::mutex> lock(pendingMutex);
      added.swap(pending);
    }
    for (auto &p : added)
    {
      if (addedLeft >= maxAdded)
        break;
      ++addedLeft;
      p.runtime = true;
      Add(p);
    }
  }

  void Clean(EntityComponentManager &_ecm)
  {
    if (robot == kNullEntity || !_ecm.HasEntity(robot))
    {
      robot = _ecm.EntityByComponents(
        components::Model(), components::Name(robotName),
        components::ParentEntity(world));
      if (robot == kNullEntity)
        return;
    }

    auto pose = worldPose(robot, _ecm);
    double rx = pose.Pos().X();
    double ry = pose.Pos().Y();
    double r2 = radius * radius;

    for (int i = Cell(rx - radius); i <= Cell(rx + radius); ++i)
    {
      for (int j = Cell(ry - radius); j <= Cell(ry + radius); ++j)
      {
        auto it = chunks.find(Key(i, j));
        if (it == chunks.end())
          continue;

        auto &pieces = it->second.pieces;
        for (size_t k = 0; k < pieces.size();)
        {
          double dx = pieces[k].x - rx;
          double dy = pieces[k].y - ry;
          if (dx * dx + dy * dy > r2)
          {
            ++k;
            continue;
          }

          stats[pieces[k].category].collected++;
          if (pieces[k].runtime)
            --addedLeft;
          scoreChanged = true;
          it->second.dirty = true;
          pieces[k] = pieces.back();
          pieces.pop_back();
        }
      }
    }
  }

  void Rebuild(EntityComponentManager &_ecm)
  {
    for (auto &[key, chunk] : chunks)
    {
      if (!chunk.dirty)
        continue;
      chunk.dirty = false;

      if (chunk.model != kNullEntity && _ecm.HasEntity(chunk.model))
        _ecm.RequestRemoveEntity(chunk.model);
      chunk.model = kNullEntity;

      if (chunk.pieces.empty())
        continue;

      // gz caches meshes by file name so every version gets a new file
      std::string name = kChunkPrefix + std::to_string(version++);
      std::string path = meshDir + "/" + name + ".obj";
      WriteMesh(chunk.pieces, path);

      // Built from SDF text so gz can serialize the model state
      sdf::Root root;
      auto errors = root.LoadSdfString(
        "<sdf version='1.8'><model name='" + name + "'><static>true</static>"
        "<link name='link'><visual name='visual'>"
        "<cast_shadows>false</cast_shadows><geometry><mesh><uri>file://" +
        path + "</uri></mesh></geometry></visual></link></model></sdf>");
      if (!errors.empty() || !root.Model())
      {
        gzerr << "vacuum_dirt: could not build chunk " << name << "\n";
        continue;
      }
      const sdf::Model &model = *root.Model();

      chunk.model = creator->CreateEntities(&model);
      creator->SetParent(chunk.model, world);
    }
  }

  // Outline of a piece in world coordinates
  static std::vector<std::vector<std::pair<double, double>>> Shape(
    const Piece &_p)
  {
    auto circle = [](double _cx, double _cy, double _rx, double _ry, int _n)
    {
      std::vector<std::pair<double, double>> poly;
      for (int i = 0; i < _n; ++i)
      {
        double a = 2.0 * M_PI * i / _n;
        poly.push_back({_cx + _rx * std::cos(a), _cy + _ry * std::sin(a)});
      }
      return poly;
    };

    std::vector<std::vector<std::pair<double, double>>> local;
    if (_p.shape == "disc")
    {
      local.push_back(circle(0, 0, _p.sx / 2, _p.sx / 2, 10));
    }
    else if (_p.shape == "paw")
    {
      // Main pad and four toes pointing along x
      double s = _p.sx;
      local.push_back(circle(-0.12 * s, 0, 0.26 * s, 0.30 * s, 12));
      local.push_back(circle(0.24 * s, 0.30 * s, 0.10 * s, 0.09 * s, 8));
      local.push_back(circle(0.34 * s, 0.10 * s, 0.11 * s, 0.09 * s, 8));
      local.push_back(circle(0.34 * s, -0.10 * s, 0.11 * s, 0.09 * s, 8));
      local.push_back(circle(0.24 * s, -0.30 * s, 0.10 * s, 0.09 * s, 8));
    }
    else
    {
      double hx = _p.sx / 2;
      double hy = _p.sy / 2;
      local.push_back({{-hx, -hy}, {hx, -hy}, {hx, hy}, {-hx, hy}});
    }

    double c = std::cos(_p.yaw);
    double s = std::sin(_p.yaw);
    for (auto &poly : local)
      for (auto &[x, y] : poly)
      {
        double wx = _p.x + c * x - s * y;
        double wy = _p.y + s * x + c * y;
        x = wx;
        y = wy;
      }
    return local;
  }

  void WriteMesh(const std::vector<Piece> &_pieces, const std::string &_path)
  {
    std::ofstream out(_path);
    out << "mtllib atlas.mtl\nusemtl dirt\nvn 0 0 1\n";

    // One texture coordinate per color at the center of its atlas cell
    for (size_t c = 0; c < kPalette.size(); ++c)
    {
      double u = (c % kAtlasCols + 0.5) / kAtlasCols;
      double v = 1.0 - (c / kAtlasCols + 0.5) / kAtlasRows;
      out << "vt " << u << " " << v << "\n";
    }

    int next = 1;
    std::ostringstream faces;
    for (const auto &p : _pieces)
    {
      for (const auto &poly : Shape(p))
      {
        for (const auto &[x, y] : poly)
          out << "v " << x << " " << y << " " << p.z << "\n";
        int vt = p.color + 1;
        for (size_t k = 1; k + 1 < poly.size(); ++k)
        {
          faces << "f " << next << "/" << vt << "/1 " << next + k << "/"
                << vt << "/1 " << next + k + 1 << "/" << vt << "/1\n";
        }
        next += poly.size();
      }
    }
    out << faces.str();
  }

  void WriteAtlas()
  {
    int w = kAtlasCols * kCellPx;
    int h = kAtlasRows * kCellPx;
    int rowBytes = w * 3;

    std::ofstream bmp(meshDir + "/atlas.bmp", std::ios::binary);
    auto u32 = [&](uint32_t v) { bmp.write(reinterpret_cast<char *>(&v), 4); };
    auto u16 = [&](uint16_t v) { bmp.write(reinterpret_cast<char *>(&v), 2); };
    bmp << "BM";
    u32(54 + rowBytes * h); u32(0); u32(54);
    u32(40); u32(w); u32(h); u16(1); u16(24); u32(0); u32(rowBytes * h);
    u32(2835); u32(2835); u32(0); u32(0);

    // BMP stores rows bottom up and pixels as BGR
    for (int y = h - 1; y >= 0; --y)
    {
      for (int x = 0; x < w; ++x)
      {
        size_t c = (y / kCellPx) * kAtlasCols + x / kCellPx;
        std::array<uint8_t, 3> rgb =
          c < kPalette.size() ? kPalette[c] : std::array<uint8_t, 3>{0, 0, 0};
        bmp.put(rgb[2]).put(rgb[1]).put(rgb[0]);
      }
    }

    std::ofstream mtl(meshDir + "/atlas.mtl");
    mtl << "newmtl dirt\nKa 1 1 1\nKd 1 1 1\nKs 0.2 0.2 0.2\nNs 20\n"
        << "map_Kd atlas.bmp\n";
  }

  void Publish(std::chrono::steady_clock::time_point _now)
  {
    int total = 0;
    int collected = 0;
    std::string categories;
    for (const auto &[name, s] : stats)
    {
      total += s.total;
      collected += s.collected;
      if (!categories.empty())
        categories += ",";
      categories += "\"" + name + "\":{\"total\":" + std::to_string(s.total) +
        ",\"collected\":" + std::to_string(s.collected) + "}";
    }

    msgs::StringMsg msg;
    msg.set_data("{\"total\":" + std::to_string(total) +
      ",\"collected\":" + std::to_string(collected) +
      ",\"categories\":{" + categories + "}}");
    scorePub.Publish(msg);
    lastPublish = _now;
    scoreChanged = false;

    if (_now - lastDensity < std::chrono::seconds(1))
      return;
    lastDensity = _now;
    std::string density = std::to_string(chunkSize);
    for (const auto &[key, chunk] : chunks)
    {
      density += ";" + std::to_string(static_cast<int32_t>(key >> 32)) + "," +
        std::to_string(static_cast<int32_t>(key & 0xffffffff)) + "," +
        std::to_string(chunk.pieces.size());
    }
    msgs::StringMsg densityMsg;
    densityMsg.set_data(density);
    densityPub.Publish(densityMsg);
  }

  static constexpr double kRebuildPeriod{0.2};
  static constexpr const char *kChunkPrefix{"vacuum_dirt_"};

  std::string robotName{"vacuum_cleaner"};
  double radius{0.15};
  double floorZ{0.0};
  double chunkSize{1.0};
  std::string topic{"/vacuum_dirt/score"};
  std::string addTopic{"/vacuum_dirt/add"};
  std::string densityTopic{"/vacuum_dirt/density"};
  std::string piecesFile;
  std::string meshDir;

  Entity world{kNullEntity};
  Entity robot{kNullEntity};
  std::unique_ptr<SdfEntityCreator> creator;

  std::unordered_map<int64_t, Chunk> chunks;
  std::map<std::string, Stats> stats;
  uint64_t version{0};
  uint64_t added{0};
  int maxAdded{2000};
  int addedLeft{0};
  double lastRebuild{0.0};
  bool needsPopulate{false};
  bool forceRebuild{true};
  bool scoreChanged{false};

  std::mutex pendingMutex;
  std::vector<Piece> pending;

  transport::Node node;
  transport::Node::Publisher scorePub;
  transport::Node::Publisher densityPub;
  std::chrono::steady_clock::time_point lastPublish;
  std::chrono::steady_clock::time_point lastDensity;
};

}  // namespace vacuum_dirt

GZ_ADD_PLUGIN(
  vacuum_dirt::VacuumDirt,
  gz::sim::System,
  vacuum_dirt::VacuumDirt::ISystemConfigure,
  vacuum_dirt::VacuumDirt::ISystemPreUpdate,
  vacuum_dirt::VacuumDirt::ISystemReset)

GZ_ADD_PLUGIN_ALIAS(vacuum_dirt::VacuumDirt, "vacuum_dirt::VacuumDirt")
