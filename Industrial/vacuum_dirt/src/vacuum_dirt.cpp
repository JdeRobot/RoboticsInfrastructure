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

#include <sdf/Geometry.hh>
#include <sdf/Link.hh>
#include <sdf/Mesh.hh>
#include <sdf/Model.hh>
#include <sdf/Visual.hh>

using namespace gz;
using namespace sim;

namespace vacuum_dirt
{

namespace fs = std::filesystem;

// Palette of the dirt atlas: 8 confetti colors in 3 shades, then two browns
// for soil and paw prints. The pieces file refers to colors by index.
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
  p.push_back({74, 52, 36});
  p.push_back({92, 66, 44});
  return p;
}();
const int kPawColor = 24;
const int kAtlasCols = 8;
const int kAtlasRows = 4;
const int kCellPx = 8;

// World system that lets a vacuum robot suck up dirt.
//
// Dirt is a list of small flat pieces (confetti flakes, streamer bits, paw
// prints). Drawing each one as its own visual makes the scene render far too
// slow beyond a few thousand pieces, so the pieces are merged into one mesh
// per square chunk of the floor (<chunk_size>, 1 m by default), each chunk
// being its own static model. When the robot center passes within <radius>
// of a piece, the piece is dropped and its chunk mesh is rewritten with the
// pieces left, so the cleaned trail follows the robot exactly.
//
// Initial dirt is read from the <pieces> file, one piece per line:
//   category shape x y yaw size_x size_y color
// shape is "rect", "disc" or "paw". More dirt can be added at runtime by
// publishing a Pose_V on <add_topic>, each pose name being the category.
//
// Progress is published as JSON on <topic>.
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
    if (_sdf->HasElement("add_topic"))
      addTopic = _sdf->Get<std::string>("add_topic");
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

    // Rebuild right away after loading too, the world starts paused
    double t = std::chrono::duration<double>(_info.simTime).count();
    if (forceRebuild || t - lastRebuild >= kRebuildPeriod || t < lastRebuild)
    {
      forceRebuild = false;
      Rebuild(_ecm);
      lastRebuild = t;
    }

    auto now = std::chrono::steady_clock::now();
    if (scoreChanged || now - lastPublish > std::chrono::seconds(1))
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
    // Start from the pieces file, dropping whatever a reset left behind
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
      double yaw = msgs::Convert(pose.orientation()).Euler().Z();
      pending.push_back({pose.name(), "paw", pose.position().x(),
        pose.position().y(), 0.0, yaw, 0.04, 0.04,
        kPawColor + static_cast<int>(pending.size() % 2)});
    }
  }

  void AddPending()
  {
    std::vector<Piece> added;
    {
      std::lock_guard<std::mutex> lock(pendingMutex);
      added.swap(pending);
    }
    for (const auto &p : added)
      Add(p);
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

      // Mesh files are cached by name, so every version needs a new one
      std::string name = kChunkPrefix + std::to_string(version++);
      std::string path = meshDir + "/" + name + ".obj";
      WriteMesh(chunk.pieces, path);

      sdf::Mesh mesh;
      mesh.SetUri("file://" + path);
      mesh.SetFilePath(path);
      sdf::Geometry geom;
      geom.SetType(sdf::GeometryType::MESH);
      geom.SetMeshShape(mesh);
      sdf::Visual visual;
      visual.SetName("visual");
      visual.SetGeom(geom);
      visual.SetCastShadows(false);
      sdf::Link sdfLink;
      sdfLink.SetName("link");
      sdfLink.AddVisual(visual);
      sdf::Model model;
      model.SetName(name);
      model.SetStatic(true);
      model.AddLink(sdfLink);

      chunk.model = creator->CreateEntities(&model);
      creator->SetParent(chunk.model, world);
    }
  }

  // Footprint of a piece as polygons in world coordinates
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
      // Main pad plus four toes, pointing along +x
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

    // One texture coordinate per palette cell, at its center
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

    // BMP rows go bottom-up and pixels are BGR
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
  }

  static constexpr double kRebuildPeriod{0.2};
  static constexpr const char *kChunkPrefix{"vacuum_dirt_"};

  std::string robotName{"vacuum_cleaner"};
  double radius{0.15};
  double floorZ{0.0};
  double chunkSize{1.0};
  std::string topic{"/vacuum_dirt/score"};
  std::string addTopic{"/vacuum_dirt/add"};
  std::string piecesFile;
  std::string meshDir;

  Entity world{kNullEntity};
  Entity robot{kNullEntity};
  std::unique_ptr<SdfEntityCreator> creator;

  std::unordered_map<int64_t, Chunk> chunks;
  std::map<std::string, Stats> stats;
  uint64_t version{0};
  uint64_t added{0};
  double lastRebuild{0.0};
  bool needsPopulate{false};
  bool forceRebuild{true};
  bool scoreChanged{false};

  std::mutex pendingMutex;
  std::vector<Piece> pending;

  transport::Node node;
  transport::Node::Publisher scorePub;
  std::chrono::steady_clock::time_point lastPublish;
};

}  // namespace vacuum_dirt

GZ_ADD_PLUGIN(
  vacuum_dirt::VacuumDirt,
  gz::sim::System,
  vacuum_dirt::VacuumDirt::ISystemConfigure,
  vacuum_dirt::VacuumDirt::ISystemPreUpdate,
  vacuum_dirt::VacuumDirt::ISystemReset)

GZ_ADD_PLUGIN_ALIAS(vacuum_dirt::VacuumDirt, "vacuum_dirt::VacuumDirt")
