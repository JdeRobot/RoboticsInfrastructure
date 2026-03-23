#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/twist.pb.h>
#include <gz/sim/components/Pose.hh>

#include <iostream>
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
    gz::transport::Node node;
    double linear_speed{0.0};
    std::mutex mtx;

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

        // Suscribirse al topic /person/cmd_vel
        this->node.Subscribe("/person/cmd_vel", &Person::OnCmdVel, this);

        std::cout << "[Person] Plugin loaded and listening to /person/cmd_vel\n";
    }

    void OnCmdVel(const gz::msgs::Twist &_msg)
    {
        std::lock_guard<std::mutex> lock(this->mtx);
        this->linear_speed = _msg.linear().x();

        if (this->linear_speed > 0.0)
            gzmsg << "[Person] Received forward speed: " << this->linear_speed << std::endl;
        else if (this->linear_speed < 0.0)
            gzmsg << "[Person] Received backward speed: " << this->linear_speed << std::endl;
        else
            gzmsg << "[Person] Received zero speed" << std::endl;
    }

    void PreUpdate(const gz::sim::UpdateInfo &_info,
                gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.paused || !this->model.Valid(_ecm))
            return;

        auto poseComp = _ecm.Component<gz::sim::components::Pose>(this->model.Entity());
        if (!poseComp)
            return;

        gz::math::Pose3d pose = poseComp->Data();

        double speed;
        {
            std::lock_guard<std::mutex> lock(this->mtx);
            speed = this->linear_speed;
        }

        double yaw = pose.Rot().Yaw();

        double dt = std::chrono::duration<double>(_info.dt).count();

        pose.Pos().X() += speed * std::cos(yaw) * dt;
        pose.Pos().Y() += speed * std::sin(yaw) * dt;

        this->model.SetWorldPoseCmd(_ecm, pose);
    }
};
}

// Registrar plugin
GZ_ADD_PLUGIN(
    person_plugin::Person,
    gz::sim::System,
    person_plugin::Person::ISystemConfigure,
    person_plugin::Person::ISystemPreUpdate
)
GZ_ADD_PLUGIN_ALIAS(person_plugin::Person, "person_plugin::Person")