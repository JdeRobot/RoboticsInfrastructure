#include <gz/sim/System.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/twist.pb.h>
#include <gz/sim/components/Pose.hh>

#include <gz/math/Quaternion.hh>

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
    gz::sim::Entity entity{gz::sim::kNullEntity};

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
                   gz::sim::EntityComponentManager &,
                   gz::sim::EventManager &) override
    {
        this->entity = _entity;

        if (this->entity == gz::sim::kNullEntity)
        {
            std::cerr << "[Person] Invalid entity\n";
            return;
        }

        this->node.Subscribe("/person/cmd_vel", &Person::OnCmdVel, this);
    }

    // ============================================
    // CALLBACK CMD_VEL
    // ============================================
    void OnCmdVel(const gz::msgs::Twist &_msg)
    {
        std::lock_guard<std::mutex> lock(this->mtx);

        this->linear_speed  = _msg.linear().x();
        this->angular_speed = _msg.angular().z();
    }

    // ============================================
    // UPDATE
    // ============================================
    void PreUpdate(const gz::sim::UpdateInfo &_info,
                   gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.paused || this->entity == gz::sim::kNullEntity)
            return;

        auto poseComp = _ecm.Component<gz::sim::components::Pose>(this->entity);
        if (!poseComp)
            return;

        gz::math::Pose3d pose = poseComp->Data();

        double lin, ang;
        {
            std::lock_guard<std::mutex> lock(this->mtx);
            lin = this->linear_speed;
            ang = this->angular_speed;
        }

        pose.Rot() = pose.Rot() * gz::math::Quaterniond(0, 0, ang);

        gz::math::Quaterniond front_offset(0, 0, -M_PI_2);

        gz::math::Vector3d forward =
            (pose.Rot() * front_offset).RotateVector(
                gz::math::Vector3d(lin, 0, 0));

        pose.Pos() += forward;

        _ecm.SetComponentData<gz::sim::components::Pose>(this->entity, pose);
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