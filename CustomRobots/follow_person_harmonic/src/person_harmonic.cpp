#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/plugin/Register.hh>

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
      double linear_speed{0.001};  // MUY pequeño para probar

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
      }

      void PreUpdate(const gz::sim::UpdateInfo &_info,
                     gz::sim::EntityComponentManager &_ecm) override
      {
        if (_info.paused || !this->model.Valid(_ecm))
          return;

        // 🔑 Leer SIEMPRE la pose actual del mundo
        auto pose = gz::sim::worldPose(this->model.Entity(), _ecm);

        double yaw = pose.Rot().Yaw();

        // Movimiento forward muy pequeño
        pose.Pos().X() += this->linear_speed * std::cos(yaw);
        pose.Pos().Y() += this->linear_speed * std::sin(yaw);

        // Aplicar movimiento
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