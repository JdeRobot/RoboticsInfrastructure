#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/plugin/Register.hh>

#include <gz/math/Pose3.hh>
#include <gz/math/Quaternion.hh>

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
    std::mutex mtx_;

    // Velocidades recibidas desde el topic
    double linear_x{0.0};
    double angular_z{0.0};

    std::shared_ptr<rclcpp::Node> node_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr sub_;

public:
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

        std::cout << "[Person] Plugin loaded\n";

        // Inicializar ROS 2 si no lo está
        if (!rclcpp::ok())
            rclcpp::init(0, nullptr);

        node_ = std::make_shared<rclcpp::Node>("person_plugin_node");

        // Suscribirse al topic de velocidades
        sub_ = node_->create_subscription<geometry_msgs::msg::Twist>(
            "/person/cmd_vel", 10,
            [this](const geometry_msgs::msg::Twist::SharedPtr msg)
            {
                std::lock_guard<std::mutex> lock(this->mtx_);
                this->linear_x = msg->linear.x;
                this->angular_z = msg->angular.z;
            });
    }

    void PreUpdate(const gz::sim::UpdateInfo &_info,
                   gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.paused || !this->model.Valid(_ecm))
            return;

        // Procesar callbacks de ROS 2
        rclcpp::spin_some(node_);

        // Obtener pose actual
        auto pose = gz::sim::worldPose(this->model.Entity(), _ecm);
        double yaw = pose.Rot().Yaw();

        double lin, ang;
        {
            std::lock_guard<std::mutex> lock(this->mtx_);
            lin = this->linear_x;
            ang = this->angular_z;
        }

        // Aplicar giro
        pose.Rot() = gz::math::Quaterniond(0, 0, yaw + ang);

        // Movimiento hacia delante según yaw
        pose.Pos().X() += lin * -std::sin(yaw);
        pose.Pos().Y() += lin *  std::cos(yaw);

        // Aplicar la nueva pose
        this->model.SetWorldPoseCmd(_ecm, pose);
    }
};
}

GZ_ADD_PLUGIN(
    person_plugin::Person,
    gz::sim::System,
    person_plugin::Person::ISystemConfigure,
    person_plugin::Person::ISystemPreUpdate
)

GZ_ADD_PLUGIN_ALIAS(person_plugin::Person, "person_plugin::Person")