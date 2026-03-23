#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/twist.pb.h>
#include <gz/sim/components/Pose.hh>

#include <gz/math/Quaternion.hh>

#include <iostream>
#include <mutex>
#include <chrono>

namespace person_plugin
{
class Person :
    public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate
{
private:
    gz::sim::Model model{gz::sim::kNullEntity};
    gz::transport::Node node;

    double linear_speed{0.0};
    double angular_speed{0.0};

    std::mutex mtx;

public:
    // ============================================
    // CONFIGURE
    // ============================================
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

        // Suscribirse al topic
        this->node.Subscribe("/person/cmd_vel", &Person::OnCmdVel, this);

        gzmsg << "[Person] Plugin loaded. Listening to /person/cmd_vel\n";
    }

    // ============================================
    // CALLBACK CMD_VEL
    // ============================================
    void OnCmdVel(const gz::msgs::Twist &_msg)
    {
        std::lock_guard<std::mutex> lock(this->mtx);

        this->linear_speed  = _msg.linear().x();
        this->angular_speed = _msg.angular().z();

        gzmsg << "[Person] lin: " << this->linear_speed
              << " | ang: " << this->angular_speed << std::endl;
    }

    // ============================================
    // UPDATE
    // ============================================
    void PreUpdate(const gz::sim::UpdateInfo &_info,
                   gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.paused || !this->model.Valid(_ecm))
            return;

        auto poseComp = _ecm.Component<gz::sim::components::Pose>(this->model.Entity());
        if (!poseComp)
            return;

        gz::math::Pose3d pose = poseComp->Data();

        double lin, ang;
        {
            std::lock_guard<std::mutex> lock(this->mtx);
            lin = this->linear_speed;
            ang = this->angular_speed;
        }

        double yaw = pose.Rot().Yaw();

        // Mover hacia adelante según yaw actual
        pose.Pos().Y() += lin * std::cos(yaw);
        pose.Pos().X() += lin * std::sin(yaw);

        // Girar según velocidad angular
        pose.Rot() = gz::math::Quaterniond(0, 0, yaw + ang);

        this->model.SetWorldPoseCmd(_ecm, pose);
    }
};
}

// ============================================
// REGISTRO DEL PLUGIN
// ============================================
GZ_ADD_PLUGIN(
    person_plugin::Person,
    gz::sim::System,
    person_plugin::Person::ISystemConfigure,
    person_plugin::Person::ISystemPreUpdate
)

GZ_ADD_PLUGIN_ALIAS(person_plugin::Person, "person_plugin::Person")