#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/plugin/Register.hh>
#include <gz/math/Pose3.hh>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>

#include <memory>
#include <mutex>

namespace person_plugin
{
class Person :
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
private:
  gz::sim::Model model{gz::sim::kNullEntity};
  std::mutex mtx;
  double forward_vel{0.0};
  double lateral_vel{0.0};
  double angular_vel{0.0};

  std::shared_ptr<rclcpp::Node> node;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr sub;

public:
  // ---------------------------------------------------------
  void Configure(const gz::sim::Entity &_entity,
                 const std::shared_ptr<const sdf::Element> &,
                 gz::sim::EntityComponentManager &_ecm,
                 gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(_entity);

    if (!this->model.Valid(_ecm))
    {
      std::cerr << "[Person] Invalid model\n";
      return;
    }

    // Crear nodo ROS 2
    if (!rclcpp::ok())
      rclcpp::init(0, nullptr);

    this->node = std::make_shared<rclcpp::Node>("person_control_node");

    // Suscribirse al topic de velocidad
    this->sub = this->node->create_subscription<geometry_msgs::msg::Twist>(
      "/person/cmd_vel", 10,
      [this](geometry_msgs::msg::Twist::SharedPtr msg)
      {
        std::lock_guard<std::mutex> lock(this->mtx);
        this->forward_vel = msg->linear.x;
        this->lateral_vel = msg->linear.y;
        this->angular_vel = msg->angular.z;
      });

    std::cout << "[Person] Plugin loaded and subscribed to /person/cmd_vel\n";
  }

  // ---------------------------------------------------------
  void PreUpdate(const gz::sim::UpdateInfo &_info,
                 gz::sim::EntityComponentManager &_ecm) override
  {
    if (_info.paused || !this->model.Valid(_ecm))
      return;

    auto pose = gz::sim::worldPose(this->model.Entity(), _ecm);

    // Lock para leer velocidad
    double fwd, lat, ang;
    {
      std::lock_guard<std::mutex> lock(this->mtx);
      fwd = this->forward_vel;
      lat = this->lateral_vel;
      ang = this->angular_vel;
    }

    double yaw = pose.Rot().Yaw();

    // Aplicar velocidad: fwd hacia adelante del robot, lat hacia la derecha
    pose.Pos().X() += fwd * std::cos(yaw) - lat * std::sin(yaw);
    pose.Pos().Y() += fwd * std::sin(yaw) + lat * std::cos(yaw);

    pose.Rot() = gz::math::Quaterniond(0, 0, yaw + ang);

    this->model.SetWorldPoseCmd(_ecm, pose);

    // Spin del nodo (no bloqueante)
    rclcpp::spin_some(this->node);
  }
};
}

// Registrar el plugin
GZ_ADD_PLUGIN(
  person_plugin::Person,
  gz::sim::System,
  person_plugin::Person::ISystemConfigure,
  person_plugin::Person::ISystemPreUpdate
)

GZ_ADD_PLUGIN_ALIAS(person_plugin::Person, "person_plugin::Person")