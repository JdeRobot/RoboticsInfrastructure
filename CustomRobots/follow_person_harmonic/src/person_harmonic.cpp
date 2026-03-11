#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/plugin/Register.hh>

#include <gz/math/Pose3.hh>
#include <gz/math/Quaternion.hh>

#include <iostream>
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

/**
 * SOCKET FUNCTIONS description (teleop)
 **/
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
    public gz::sim::ISystemPostUpdate
  {
    private:
      // ===== Movement state =====
      int current_wp{0};
      int turn_dir{0};
      int linear_dir{0};

      bool auto_movement{true};
      bool linear_movement{true};

      float lv_dt{0.001f};   // discrete linear velocity
      float av_dt{0.003f};   // discrete angular velocity

      // variables to use in MoveToWaypoint method
      bool orientation_reached{false};
      bool direction_chosen{false};

      // ===== Gazebo Harmonic entities =====
      gz::sim::Model model{gz::sim::kNullEntity};

      // Cached pose read from PostUpdate
      gz::math::Pose3d currentPose{0, 0, 0, 0, 0, 0};
      bool poseInitialized{false};

      // waypoints where (px, py, next_waypoint)
      std::vector<std::tuple<float, float, int>> wp;

      // quadrants vector to know the correct direction of turn
      std::vector<std::tuple<float, float>> quadrants;

      // ===== UDP server =====
      int sockfd{-1};
      struct sockaddr_in addr{};
      std::thread server_thread;
      std::atomic<bool> running{false};

      // Protect shared state between server thread and sim thread
      std::mutex mtx;

    private:
      float GetDistanceEuclidean(float rx, float ry)
      {
        std::lock_guard<std::mutex> lock(this->mtx);
        return std::sqrt(
          std::pow(this->currentPose.Pos().X() - rx, 2.0) +
          std::pow(this->currentPose.Pos().Y() - ry, 2.0));
      }

      float GetDistanceEuclidean(std::tuple<float, float, int> & waypoint)
      {
        float wx = std::get<0>(waypoint);
        float wy = std::get<1>(waypoint);
        return GetDistanceEuclidean(wx, wy);
      }

      int GetNearestWaypoint(std::vector<std::tuple<float, float, int>> & waypoints)
      {
        float current_dist;
        int nearest_index = 0;
        float min_dist = GetDistanceEuclidean(waypoints[0]);

        for (size_t i = 0; i < waypoints.size(); i++)
        {
          current_dist = GetDistanceEuclidean(waypoints[i]);
          if (current_dist < min_dist)
          {
            min_dist = current_dist;
            nearest_index = static_cast<int>(i);
          }
        }

        return nearest_index;
      }

      float GetAngle(float rx, float ry)
      {
        // Preservo tu lógica original para mantener el comportamiento
        std::lock_guard<std::mutex> lock(this->mtx);
        float px = static_cast<float>(this->currentPose.Pos().X());
        float py = static_cast<float>(this->currentPose.Pos().Y());

        float angle = std::atan2(std::abs(rx - px), std::abs(ry - py));

        if (ry > py)
          angle = PI - angle;

        if (rx < px)
          angle *= -1.0f;

        return angle;
      }

      int GetBestTurnDirection(float desired_yaw, float actual_yaw)
      {
        auto get_quadrant = [](float yaw,
                               const std::vector<std::tuple<float, float>> & quadrants) -> int
        {
          for (std::size_t i = 0; i < QUADRANTS; i++)
          {
            if (yaw >= std::get<0>(quadrants[i]) && yaw < std::get<1>(quadrants[i]))
              return static_cast<int>(i);
          }

          // borde numérico: yaw == PI
          if (std::abs(yaw - PI) < 1e-6)
            return 1;

          return 0;
        };

        int actual_quadrant = get_quadrant(actual_yaw, this->quadrants);
        int desired_quadrant = get_quadrant(desired_yaw, this->quadrants);

        if (actual_quadrant == desired_quadrant)
          return (desired_yaw > actual_yaw) ? 1 : -1;

        int n1, n2;
        float dist1, dist2;

        n1 = (desired_quadrant > actual_quadrant) ?
              desired_quadrant - actual_quadrant :
              QUADRANTS - std::abs((desired_quadrant - actual_quadrant) % QUADRANTS);
        n2 = QUADRANTS - n1;

        dist1 = std::get<1>(quadrants[actual_quadrant]) - actual_yaw;
        for (int i = 0; i < (n1 - 1); i++)
          dist1 += PI / 2.0f;
        dist1 += desired_yaw - std::get<0>(quadrants[desired_quadrant]);

        dist2 = actual_yaw - std::get<0>(quadrants[actual_quadrant]);
        for (int i = 0; i < (n2 - 1); i++)
          dist2 += PI / 2.0f;
        dist2 += std::get<1>(quadrants[desired_quadrant]) - desired_yaw;

        return (dist1 <= dist2) ? 1 : -1;
      }

      bool MoveToWaypoint(std::tuple<float, float, int> & waypoint,
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

        // 1) choose turning direction once
        if (!direction_chosen)
        {
          direction_chosen = true;
          turn_dir = GetBestTurnDirection(angle,
                     static_cast<float>(pose.Rot().Yaw()));
        }

        // 2) rotate until desired yaw
        if (!orientation_reached)
        {
          pose.Rot() = gz::math::Quaterniond(
            0, 0, pose.Rot().Yaw() + turn_dir * av_dt);

          if (std::abs(angle - pose.Rot().Yaw()) < 0.005f)
            orientation_reached = true;
        }
        // 3) move forward
        else
        {
          pose.Pos().X() += -lv_dt * (0 * std::cos(pose.Rot().Yaw()) -
                                      1 * std::sin(pose.Rot().Yaw()));
          pose.Pos().Y() += -lv_dt * (0 * std::sin(pose.Rot().Yaw()) +
                                      1 * std::cos(pose.Rot().Yaw()));
        }

        // Command new pose in Harmonic
        this->model.SetWorldPoseCmd(_ecm, pose);

        {
          std::lock_guard<std::mutex> lock(this->mtx);
          this->currentPose = pose;
        }

        if (orientation_reached && GetDistanceEuclidean(rx, ry) < 0.1f)
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

        while (this->running.load())
        {
          std::memset(msg, 0, sizeof(msg));
          int ret = recv_message(this->sockfd, this->addr, &msg, sizeof(msg));
          if (ret != 0)
            continue;

          std::lock_guard<std::mutex> lock(this->mtx);

          if (msg[0] == 'U')
          {
            auto_movement = false;

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
          else if (msg[0] == 'A')
          {
            current_wp = GetNearestWaypoint(this->wp);
            auto_movement = true;
            orientation_reached = false;
            direction_chosen = false;
          }
        }
      }

    public:
      Person() = default;

      ~Person() override
      {
        this->running.store(false);

        if (this->sockfd >= 0)
        {
          // desbloquea recvfrom al cerrar
          close_socket(this->sockfd);
          this->sockfd = -1;
        }

        if (this->server_thread.joinable())
          this->server_thread.join();
      }

      void Configure(const gz::sim::Entity &_entity,
                     const std::shared_ptr<const sdf::Element> & /*_sdf*/,
                     gz::sim::EntityComponentManager &_ecm,
                     gz::sim::EventManager & /*_eventMgr*/) override
      {
        this->model = gz::sim::Model(_entity);

        if (!this->model.Valid(_ecm))
        {
          std::cerr << "[Person] Plugin must be attached to a model.\n";
          return;
        }

        this->currentPose = gz::sim::worldPose(this->model.Entity(), _ecm);
        this->poseInitialized = true;

        std::cout << "Initial Position Person [" << this->currentPose << "]\n";

        // WayPoints
        this->current_wp = 0;
        this->wp = {
          std::make_tuple(4, 6, 1),
          std::make_tuple(5, 3, 2),
          std::make_tuple(5, -14.5, 3),
          std::make_tuple(-5, -14.5, 4),
          std::make_tuple(-5, -25, 5),
          std::make_tuple(5, -25, 6),
          std::make_tuple(5, -14.5, 7),
          std::make_tuple(-5, -14.5, 8),
          std::make_tuple(-5, -1, 9),
          std::make_tuple(-4, 2, 10),
          std::make_tuple(-4, 5, 11),
          std::make_tuple(-2.5, 13, 12),
          std::make_tuple(3, 13, 13),
          std::make_tuple(4, 10, 0),
        };

        this->quadrants = {
          std::make_tuple(0.0f, PI / 2.0f),
          std::make_tuple(PI / 2.0f, PI),
          std::make_tuple(-PI, -PI / 2.0f),
          std::make_tuple(-PI / 2.0f, 0.0f)
        };

        this->auto_movement = true;
        this->linear_movement = true;
        this->linear_dir = 0;
        this->turn_dir = 0;
        this->orientation_reached = false;
        this->direction_chosen = false;

        // UDP server
        this->sockfd = create_socket();
        set_ip_port(this->addr, IP.c_str(), PORT);
        make_bind(this->sockfd, this->addr);

        this->running.store(true);
        this->server_thread = std::thread(&Person::ServerThreadLoop, this);
      }

      void PreUpdate(const gz::sim::UpdateInfo &_info,
                     gz::sim::EntityComponentManager &_ecm) override
      {
        if (_info.paused || !this->poseInitialized || !this->model.Valid(_ecm))
          return;

        bool localAuto;
        bool localLinearMovement;
        int localCurrentWp;
        int localLinearDir;
        int localTurnDir;

        {
          std::lock_guard<std::mutex> lock(this->mtx);
          localAuto = this->auto_movement;
          localLinearMovement = this->linear_movement;
          localCurrentWp = this->current_wp;
          localLinearDir = this->linear_dir;
          localTurnDir = this->turn_dir;
        }

        if (localAuto)
        {
          if (MoveToWaypoint(this->wp[localCurrentWp], _ecm))
          {
            std::lock_guard<std::mutex> lock(this->mtx);
            this->current_wp = std::get<2>(this->wp[this->current_wp]);
          }
        }
        else
        {
          gz::math::Pose3d pose;
          {
            std::lock_guard<std::mutex> lock(this->mtx);
            pose = this->currentPose;
          }

          if (localLinearMovement)
          {
            pose.Pos().X() += -(localLinearDir) * lv_dt *
                              (0 * std::cos(pose.Rot().Yaw()) -
                               1 * std::sin(pose.Rot().Yaw()));
            pose.Pos().Y() += -(localLinearDir) * lv_dt *
                              (0 * std::sin(pose.Rot().Yaw()) +
                               1 * std::cos(pose.Rot().Yaw()));
          }
          else
          {
            pose.Rot() = gz::math::Quaterniond(
              0, 0, pose.Rot().Yaw() + localTurnDir * av_dt);
          }

          this->model.SetWorldPoseCmd(_ecm, pose);

          {
            std::lock_guard<std::mutex> lock(this->mtx);
            this->currentPose = pose;
          }
        }
      }

      void PostUpdate(const gz::sim::UpdateInfo & /*_info*/,
                      const gz::sim::EntityComponentManager &_ecm) override
      {
        if (!this->model.Valid(_ecm))
          return;

        auto pose = gz::sim::worldPose(this->model.Entity(), _ecm);

        std::lock_guard<std::mutex> lock(this->mtx);
        this->currentPose = pose;
        this->poseInitialized = true;
      }
  };
}

GZ_ADD_PLUGIN(
  person_plugin::Person,
  gz::sim::System,
  person_plugin::Person::ISystemConfigure,
  person_plugin::Person::ISystemPreUpdate,
  person_plugin::Person::ISystemPostUpdate
)

GZ_ADD_PLUGIN_ALIAS(person_plugin::Person, "person_plugin::Person")

/**
 * SOCKETS FUNCTIONS Definitions
 **/

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
  if (recvfrom(fd, buf, len, 0, (struct sockaddr *)&dest_addr, &socklen) == -1)
  {
    warn("recvfrom failed");
    return 1;
  }
  return 0;
}
