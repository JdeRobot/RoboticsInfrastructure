#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/math/Pose3.hh>

#include <iostream>

namespace person_plugin
{
  class Person:
    public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate
  {
    private:
      gz::sim::Model model{gz::sim::kNullEntity};
      gz::transport::Node node;
      double linear_speed{0.0}; // velocidad recibida del topic

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

        // Suscribirse al topic /cmd_vel
        this->node.Subscribe("/cmd_vel", &Person::OnCmdVel, this);

        std::cout << "[Person] Plugin loaded\n";
      }

      // Callback que guarda la velocidad lineal
      void OnCmdVel(const gz::msgs::Twist &_msg)
      {
        this->linear_speed = _msg.linear().x();
      }

      void PreUpdate(const gz::sim::UpdateInfo &_info,
                     gz::sim::EntityComponentManager &_ecm) override
      {
        if (_info.paused || !this->model.Valid(_ecm))
          return;

        // Leer pose actual del mundo
        auto pose = gz::sim::worldPose(this->model.Entity(), _ecm);
        double yaw = pose.Rot().Yaw();

        // Mover hacia adelante según linear_speed
        pose.Pos().X() += this->linear_speed * std::cos(yaw);
        pose.Pos().Y() += this->linear_speed * std::sin(yaw);

        // Aplicar nueva pose
        this->model.SetWorldPoseCmd(_ecm, pose);
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