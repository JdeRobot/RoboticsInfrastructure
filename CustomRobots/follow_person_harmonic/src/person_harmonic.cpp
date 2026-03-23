#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/plugin/Register.hh>

#include <iostream>

namespace person_plugin
{
  class Person:
    public gz::sim::System,
    public gz::sim::ISystemConfigure
  {
    private:
      gz::sim::Model model{gz::sim::kNullEntity};

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

        std::cout << "[Person] Plugin loaded correctly\n";
      }
  };
}

GZ_ADD_PLUGIN(
  person_plugin::Person,
  gz::sim::System,
  person_plugin::Person::ISystemConfigure
)

GZ_ADD_PLUGIN_ALIAS(person_plugin::Person, "person_plugin::Person")