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
#include <chrono>
#include <iostream>

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

      gz::math::Pose3d currentPose{0, 0, 0, 0, 0, 0};
      bool poseInitialized{false};

      gz::math::Pose3d initialPose{0, 0, 0, 0, 0, 0};
      bool initialPoseInitialized{false};

      std::vector<std::tuple<float, float, int>> wp;
      std::vector<std::tuple<float, float>> quadrants;

      int sockfd{-1};
      struct sockaddr_in addr{};
      std::thread server_thread;
      std::atomic<bool> running{false};

      std::mutex mtx;

      std::chrono::steady_clock::time_point last_auto_toggle{
        std::chrono::steady_clock::now()};
      std::chrono::milliseconds auto_toggle_cooldown{250};

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

      float GetDistanceEuclidean(const std::tuple<float, float, int> & waypoint)
      {
        return GetDistanceEuclidean(std::get<0>(waypoint), std::get<1>(waypoint));
      }

      int GetNearestWaypoint(const std::vector<std::tuple<float, float, int>> & waypoints)
      {
        int nearest_index = 0;
        float min_dist = GetDistanceEuclidean(waypoints[0]);

        for (size_t i = 1; i < waypoints.size(); ++i)
        {
          float current_dist = GetDistanceEuclidean(waypoints[i]);
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
        gz::math::Pose3d pose;
        {
          std::lock_guard<std::mutex> lock(this->mtx);
          pose = this->currentPose;
        }

        float px = static_cast<float>(pose.Pos().X());
        float py = static_cast<float>(pose.Pos().Y());

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
          [](float yaw, const std::vector<std::tuple<float, float>> & quadrants) -> int
        {
          for (std::size_t i = 0; i < QUADRANTS; ++i)
          {
            if (yaw >= std::get<0>(quadrants[i]) &&
                yaw < std::get<1>(quadrants[i]))
            {
              return static_cast<int>(i);
            }
          }

          if (std::abs(yaw - PI) < 1e-6)
            return 1;

          return 0;
        };

        int actual_quadrant = get_quadrant(actual_yaw, this->quadrants);
        int desired_quadrant = get_quadrant(desired_yaw, this->quadrants);

        if (actual_quadrant == desired_quadrant)
          return (desired_yaw > actual_yaw) ? 1 : -1;

        int n1 =
          (desired_quadrant > actual_quadrant) ?
          desired_quadrant - actual_quadrant :
          QUADRANTS - std::abs((desired_quadrant - actual_quadrant) % QUADRANTS);

        int n2 = QUADRANTS - n1;

        float dist1 = std::get<1>(this->quadrants[actual_quadrant]) - actual_yaw;
        for (int i = 0; i < (n1 - 1); ++i)
          dist1 += PI / 2.0f;
        dist1 += desired_yaw - std::get<0>(this->quadrants[desired_quadrant]);

        float dist2 = actual_yaw - std::get<0>(this->quadrants[actual_quadrant]);
        for (int i = 0; i < (n2 - 1); ++i)
          dist2 += PI / 2.0f;
        dist2 += std::get<1>(this->quadrants[desired_quadrant]) - desired_yaw;

        return (dist1 <= dist2) ? 1 : -1;
      }

      bool MoveToWaypoint(const std::tuple<float, float, int> & waypoint,
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

        if (!this->direction_chosen)
        {
          this->direction_chosen = true;
          this->turn_dir = GetBestTurnDirection(
            angle,
            static_cast<float>(pose.Rot().Yaw()));
        }

        if (!this->orientation_reached)
        {
          pose.Rot() = gz::math::Quaterniond(
            0,
            0,
            pose.Rot().Yaw() + this->turn_dir * this->av_dt);

          if (std::abs(angle - pose.Rot().Yaw()) < 0.005f)
            this->orientation_reached = true;
        }
        else
        {
          pose.Pos().X() += -this->lv_dt *
                            (0 * std::cos(pose.Rot().Yaw()) -
                             1 * std::sin(pose.Rot().Yaw()));
          pose.Pos().Y() += -this->lv_dt *
                            (0 * std::sin(pose.Rot().Yaw()) +
                             1 * std::cos(pose.Rot().Yaw()));
        }

        this->model.SetWorldPoseCmd(_ecm, pose);

        {
          std::lock_guard<std::mutex> lock(this->mtx);
          this->currentPose = pose;
        }

        if (this->orientation_reached && GetDistanceEuclidean(rx, ry) < 0.1f)
        {
          this->orientation_reached = false;
          this->direction_chosen = false;
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

          if (msg[0] != 'U')
            continue;

          if (this->auto_movement)
          {
            if (msg[1] == 'S')
              continue;

            auto now = std::chrono::steady_clock::now();
            if (now - this->last_auto_toggle < this->auto_toggle_cooldown)
              continue;

            this->last_auto_toggle = now;
            this->auto_paused = !this->auto_paused;
            this->linear_dir = 0;
            this->turn_dir = 0;
            this->linear_movement = true;
            continue;
          }

          if (msg[1] == 'V')
          {
            this->linear_movement = true;
            if (msg[2] == 'F')
              this->linear_dir = 1;
            else if (msg[2] == 'B')
              this->linear_dir = -1;
          }
          else if (msg[1] == 'A')
          {
            this->linear_movement = false;
            if (msg[2] == 'R')
              this->turn_dir = -1;
            else if (msg[2] == 'L')
              this->turn_dir = 1;
          }
          else if (msg[1] == 'S')
          {
            this->linear_dir = 0;
            this->turn_dir = 0;
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
          close_socket(this->sockfd);
          this->sockfd = -1;
        }

        if (this->server_thread.joinable())
          this->server_thread.join();
      }

      void Configure(const gz::sim::Entity &_entity,
                     const std::shared_ptr<const sdf::Element> &_sdf,
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
        this->initialPose = this->currentPose;
        this->initialPoseInitialized = true;

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

        if (_sdf && _sdf->HasElement("auto_movement"))
          this->auto_movement = _sdf->Get<bool>("auto_movement");
        else
          this->auto_movement = true;

        this->auto_paused = this->auto_movement;
        this->initial_auto_movement = this->auto_movement;
        this->initial_auto_paused = this->auto_paused;

        this->linear_movement = true;
        this->linear_dir = 0;
        this->turn_dir = 0;
        this->orientation_reached = false;
        this->direction_chosen = false;
        this->last_auto_toggle = std::chrono::steady_clock::now();

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
        bool localAutoPaused;
        bool localLinearMovement;
        int localCurrentWp;
        int localLinearDir;
        int localTurnDir;

        {
          std::lock_guard<std::mutex> lock(this->mtx);
          localAuto = this->auto_movement;
          localAutoPaused = this->auto_paused;
          localLinearMovement = this->linear_movement;
          localCurrentWp = this->current_wp;
          localLinearDir = this->linear_dir;
          localTurnDir = this->turn_dir;
        }

        if (localAuto)
        {
          if (localAutoPaused)
            return;

          if (MoveToWaypoint(this->wp[localCurrentWp], _ecm))
          {
            std::lock_guard<std::mutex> lock(this->mtx);
            this->current_wp = std::get<2>(this->wp[this->current_wp]);
          }

          return;
        }

        gz::math::Pose3d pose;
        {
          std::lock_guard<std::mutex> lock(this->mtx);
          pose = this->currentPose;
        }

        if (localLinearMovement)
        {
          pose.Pos().X() += -(localLinearDir) * this->lv_dt *
                            (0 * std::cos(pose.Rot().Yaw()) -
                             1 * std::sin(pose.Rot().Yaw()));
          pose.Pos().Y() += -(localLinearDir) * this->lv_dt *
                            (0 * std::sin(pose.Rot().Yaw()) +
                             1 * std::cos(pose.Rot().Yaw()));
        }
        else
        {
          pose.Rot() = gz::math::Quaterniond(
            0,
            0,
            pose.Rot().Yaw() + localTurnDir * this->av_dt);
        }

        this->model.SetWorldPoseCmd(_ecm, pose);

        {
          std::lock_guard<std::mutex> lock(this->mtx);
          this->currentPose = pose;
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

          // ---- TRAZA DE POSICION ----
        std::cout << "PERSON_POSE "
            << pose.Pos().X() << " "
            << pose.Pos().Y() << std::endl;
      }

      void Reset(const gz::sim::UpdateInfo & /*_info*/,
                 gz::sim::EntityComponentManager &_ecm) override
      {
        if (!this->model.Valid(_ecm) || !this->initialPoseInitialized)
          return;

        {
          std::lock_guard<std::mutex> lock(this->mtx);
          this->currentPose = this->initialPose;
          this->current_wp = 0;
          this->turn_dir = 0;
          this->linear_dir = 0;
          this->auto_movement = this->initial_auto_movement;
          this->auto_paused = this->initial_auto_paused;
          this->linear_movement = true;
          this->orientation_reached = false;
          this->direction_chosen = false;
          this->last_auto_toggle = std::chrono::steady_clock::now();
        }

        this->model.SetWorldPoseCmd(_ecm, this->initialPose);
      }
  };
}

GZ_ADD_PLUGIN(
  person_plugin::Person,
  gz::sim::System,
  person_plugin::Person::ISystemConfigure,
  person_plugin::Person::ISystemPreUpdate,
  person_plugin::Person::ISystemPostUpdate,
  person_plugin::Person::ISystemReset
)

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
  if (recvfrom(fd, buf, len, 0, (struct sockaddr *)&dest_addr, &socklen) == -1)
  {
    warn("recvfrom failed");
    return 1;
  }
  return 0;
}
