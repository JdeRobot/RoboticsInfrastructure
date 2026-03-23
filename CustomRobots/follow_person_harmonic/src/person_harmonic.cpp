#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/twist.pb.h>
#include <gz/sim/components/Pose.hh>

#include <iostream>

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

        std::cout << "[Person] Plugin loaded\n";
    }

    void OnCmdVel(const gz::msgs::Twist &_msg)
    {
        this->linear_speed = _msg.linear().x();
    }

    void PreUpdate(const gz::sim::UpdateInfo &_info,
                  gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.paused || !this->model.Valid(_ecm))
            return;

        // Obtener pose actual
        auto poseComp = _ecm.Component<gz::sim::components::Pose>(this->model.Entity());
        if (!poseComp)
            return;

        auto pose = poseComp->Data();
        double yaw = pose.Rot().Yaw();

        // Si linear_speed es positivo → mover hacia delante
        if (this->linear_speed > 0.0)
        {
            pose.Pos().X() += this->linear_speed * std::cos(yaw);
            pose.Pos().Y() += this->linear_speed * std::sin(yaw);
        }
        // Si linear_speed es negativo → mover hacia atrás
        else if (this->linear_speed < 0.0)
        {
            pose.Pos().X() += this->linear_speed * std::cos(yaw);  // linear_speed negativo
            pose.Pos().Y() += this->linear_speed * std::sin(yaw);
        }
        // Si linear_speed == 0 → no hacer nada

        // Aplicar nueva pose
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