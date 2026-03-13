#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/plugin/Register.hh>

#include <gz/math/Pose3.hh>
#include <gz/math/Quaternion.hh>

#include <vector>
#include <tuple>
#include <cmath>
#include <thread>
#include <mutex>
#include <atomic>
#include <cstring>

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <err.h>

int create_socket(void);
void close_socket(int fd);
void set_ip_port(struct sockaddr_in & addr, const char * ip, int port);
void make_bind(int fd, struct sockaddr_in & addr);
int recv_message(int fd, struct sockaddr_in & dest_addr, void * buf, size_t len);

const float PI = 3.14159265f;
const int QUADRANTS = 4;
const std::string IP = "0.0.0.0";
const int PORT = 36677;

namespace person_plugin
{

class Person:
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate,
  public gz::sim::ISystemPostUpdate,
  public gz::sim::ISystemReset
{
private:

  int current_wp{0};

  int turn_dir{0};
  int linear_dir{0};

  bool auto_movement{true};
  bool auto_paused{true};
  bool linear_movement{true};

  bool initial_auto_movement{true};
  bool initial_auto_paused{true};

  float lv_dt{0.001f};
  float av_dt{0.003f};

  bool orientation_reached{false};
  bool direction_chosen{false};

  gz::sim::Model model{gz::sim::kNullEntity};

  gz::math::Pose3d currentPose{0,0,0,0,0,0};
  bool poseInitialized{false};

  gz::math::Pose3d initialPose{0,0,0,0,0,0};
  bool initialPoseInitialized{false};

  std::vector<std::tuple<float,float,int>> wp;
  std::vector<std::tuple<float,float>> quadrants;

  int sockfd{-1};
  struct sockaddr_in addr{};
  std::thread server_thread;
  std::atomic<bool> running{false};

  std::mutex mtx;

private:

  float GetDistanceEuclidean(float rx, float ry)
  {
    gz::math::Pose3d pose;

    {
      std::lock_guard<std::mutex> lock(this->mtx);
      pose = this->currentPose;
    }

    return std::sqrt(
      std::pow(pose.Pos().X() - rx, 2.0) +
      std::pow(pose.Pos().Y() - ry, 2.0));
  }

  float GetDistanceEuclidean(const std::tuple<float,float,int> & waypoint)
  {
    return GetDistanceEuclidean(
      std::get<0>(waypoint),
      std::get<1>(waypoint));
  }

  float GetAngle(float rx, float ry)
  {
    gz::math::Pose3d pose;

    {
      std::lock_guard<std::mutex> lock(this->mtx);
      pose = this->currentPose;
    }

    float px = pose.Pos().X();
    float py = pose.Pos().Y();

    float angle = std::atan2(std::abs(rx - px), std::abs(ry - py));

    if (ry > py)
      angle = PI - angle;

    if (rx < px)
      angle *= -1.0f;

    return angle;
  }

  int GetBestTurnDirection(float desired_yaw, float actual_yaw)
  {
    auto get_quadrant =
      [](float yaw,
         const std::vector<std::tuple<float,float>> & quadrants)
      {
        for (int i = 0; i < QUADRANTS; i++)
        {
          if (yaw >= std::get<0>(quadrants[i]) &&
              yaw <  std::get<1>(quadrants[i]))
            return i;
        }

        if (std::abs(yaw - PI) < 1e-6)
          return 1;

        return 0;
      };

    int aq = get_quadrant(actual_yaw, this->quadrants);
    int dq = get_quadrant(desired_yaw, this->quadrants);

    if (aq == dq)
      return (desired_yaw > actual_yaw) ? 1 : -1;

    int n1 =
      (dq > aq) ?
      dq - aq :
      QUADRANTS - std::abs((dq - aq) % QUADRANTS);

    int n2 = QUADRANTS - n1;

    float dist1 =
      std::get<1>(quadrants[aq]) - actual_yaw;

    for (int i = 0; i < (n1 - 1); i++)
      dist1 += PI / 2.0f;

    dist1 += desired_yaw - std::get<0>(quadrants[dq]);

    float dist2 =
      actual_yaw - std::get<0>(quadrants[aq]);

    for (int i = 0; i < (n2 - 1); i++)
      dist2 += PI / 2.0f;

    dist2 += std::get<1>(quadrants[dq]) - desired_yaw;

    return (dist1 <= dist2) ? 1 : -1;
  }

  bool MoveToWaypoint(
    const std::tuple<float,float,int> & waypoint,
    gz::sim::EntityComponentManager &_ecm)
  {
    float rx = std::get<0>(waypoint);
    float ry = std::get<1>(waypoint);

    float angle = GetAngle(rx, ry);

    gz::math::Pose3d pose;

    {
      std::lock_guard<std::mutex> lock(this->mtx);
      pose = this->currentPose;
    }

    if (!direction_chosen)
    {
      direction_chosen = true;
      turn_dir =
        GetBestTurnDirection(angle,
          pose.Rot().Yaw());
    }

    if (!orientation_reached)
    {
      pose.Rot() =
        gz::math::Quaterniond(
          0,
          0,
          pose.Rot().Yaw() + turn_dir * av_dt);

      if (std::abs(angle - pose.Rot().Yaw()) < 0.005f)
        orientation_reached = true;
    }
    else
    {
      pose.Pos().X() +=
        -lv_dt * (-std::sin(pose.Rot().Yaw()));

      pose.Pos().Y() +=
        -lv_dt * ( std::cos(pose.Rot().Yaw()));
    }

    model.SetWorldPoseCmd(_ecm, pose);

    {
      std::lock_guard<std::mutex> lock(this->mtx);
      currentPose = pose;
    }

    if (orientation_reached &&
        GetDistanceEuclidean(rx, ry) < 0.1f)
    {
      orientation_reached = false;
      direction_chosen = false;
      return true;
    }

    return false;
  }

  void ServerThreadLoop()
  {
    char msg[3];

    while (running.load())
    {
      std::memset(msg, 0, sizeof(msg));

      int ret =
        recv_message(sockfd, addr, &msg, sizeof(msg));

      if (ret != 0)
        continue;

      std::lock_guard<std::mutex> lock(mtx);

      if (msg[0] != 'U')
        continue;

      if (auto_movement)
      {
        if (msg[1] == 'S')
          continue;

        auto_paused = !auto_paused;
        continue;
      }

      if (msg[1] == 'V')
      {
        linear_movement = true;

        if (msg[2] == 'F')
          linear_dir = 1;

        else if (msg[2] == 'B')
          linear_dir = -1;
      }

      else if (msg[1] == 'A')
      {
        linear_movement = false;

        if (msg[2] == 'R')
          turn_dir = -1;

        else if (msg[2] == 'L')
          turn_dir = 1;
      }

      else if (msg[1] == 'S')
      {
        linear_dir = 0;
        turn_dir = 0;
      }
    }
  }

public:

  Person() = default;

  ~Person() override
  {
    running.store(false);

    if (sockfd >= 0)
    {
      close_socket(sockfd);
      sockfd = -1;
    }

    if (server_thread.joinable())
      server_thread.join();
  }

  void Configure(
    const gz::sim::Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &_ecm,
    gz::sim::EventManager &) override
  {
    model = gz::sim::Model(_entity);

    currentPose =
      gz::sim::worldPose(model.Entity(), _ecm);

    poseInitialized = true;

    initialPose = currentPose;
    initialPoseInitialized = true;

    if (_sdf && _sdf->HasElement("auto_movement"))
      auto_movement = _sdf->Get<bool>("auto_movement");

    auto_paused = auto_movement;

    initial_auto_movement = auto_movement;
    initial_auto_paused = auto_paused;

    wp = {
      {4,6,1},
      {5,3,2},
      {5,-14.5,3},
      {-5,-14.5,4},
      {-5,-25,5},
      {5,-25,6},
      {5,-14.5,7},
      {-5,-14.5,8},
      {-5,-1,9},
      {-4,2,10},
      {-4,5,11},
      {-2.5,13,12},
      {3,13,13},
      {4,10,0}
    };

    quadrants = {
      {0.0f, PI/2.0f},
      {PI/2.0f, PI},
      {-PI, -PI/2.0f},
      {-PI/2.0f, 0.0f}
    };

    sockfd = create_socket();
    set_ip_port(addr, IP.c_str(), PORT);
    make_bind(sockfd, addr);

    running.store(true);
    server_thread =
      std::thread(&Person::ServerThreadLoop, this);
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager &_ecm) override
  {
    if (_info.paused ||
        !poseInitialized)
      return;

    bool localAuto;
    bool localPaused;
    int localWP;

    {
      std::lock_guard<std::mutex> lock(mtx);
      localAuto = auto_movement;
      localPaused = auto_paused;
      localWP = current_wp;
    }

    if (localAuto)
    {
      if (localPaused)
        return;

      if (MoveToWaypoint(wp[localWP], _ecm))
      {
        std::lock_guard<std::mutex> lock(mtx);
        current_wp = std::get<2>(wp[current_wp]);
      }

      return;
    }

    gz::math::Pose3d pose;

    {
      std::lock_guard<std::mutex> lock(mtx);
      pose = currentPose;
    }

    if (linear_movement)
    {
      pose.Pos().X() +=
        -(linear_dir) * lv_dt *
        (-std::sin(pose.Rot().Yaw()));

      pose.Pos().Y() +=
        -(linear_dir) * lv_dt *
        ( std::cos(pose.Rot().Yaw()));
    }
    else
    {
      pose.Rot() =
        gz::math::Quaterniond(
          0,
          0,
          pose.Rot().Yaw() + turn_dir * av_dt);
    }

    model.SetWorldPoseCmd(_ecm, pose);

    {
      std::lock_guard<std::mutex> lock(mtx);
      currentPose = pose;
    }
  }

  void PostUpdate(
    const gz::sim::UpdateInfo &,
    const gz::sim::EntityComponentManager &_ecm) override
  {
    auto pose =
      gz::sim::worldPose(model.Entity(), _ecm);

    std::lock_guard<std::mutex> lock(mtx);
    currentPose = pose;
  }

  void Reset(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &_ecm) override
  {
    std::lock_guard<std::mutex> lock(mtx);

    currentPose = initialPose;
    current_wp = 0;
    turn_dir = 0;
    linear_dir = 0;

    auto_movement = initial_auto_movement;
    auto_paused = initial_auto_paused;

    orientation_reached = false;
    direction_chosen = false;

    model.SetWorldPoseCmd(_ecm, initialPose);
  }
};

}

GZ_ADD_PLUGIN(
  person_plugin::Person,
  gz::sim::System,
  person_plugin::Person::ISystemConfigure,
  person_plugin::Person::ISystemPreUpdate,
  person_plugin::Person::ISystemPostUpdate,
  person_plugin::Person::ISystemReset)

GZ_ADD_PLUGIN_ALIAS(person_plugin::Person, "person_plugin::Person")

int create_socket(void)
{
  int fd = socket(AF_INET, SOCK_DGRAM, 0);
  if (fd == -1)
    err(1, "socket failed");
  return fd;
}

void close_socket(int fd)
{
  if (close(fd) == -1)
    err(1, "close failed");
}

void set_ip_port(struct sockaddr_in & addr, const char * ip, int port)
{
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = inet_addr(ip);
  addr.sin_port = htons(port);
}

void make_bind(int fd, struct sockaddr_in & addr)
{
  if (bind(fd, (struct sockaddr *)&addr, sizeof addr) == -1)
    err(1, "bind failed");
}

int recv_message(int fd, struct sockaddr_in & dest_addr, void * buf, size_t len)
{
  socklen_t socklen = sizeof dest_addr;

  if (recvfrom(fd, buf, len, 0,
               (struct sockaddr *)&dest_addr,
               &socklen) == -1)
  {
    warn("recvfrom failed");
    return 1;
  }

  return 0;
}
