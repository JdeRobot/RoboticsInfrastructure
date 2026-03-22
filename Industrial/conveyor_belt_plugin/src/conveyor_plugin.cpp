#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/components/LinearVelocity.hh>
#include <gz/plugin/Register.hh>

namespace conveyor
{

class ConveyorPlugin :
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  double velocity{0.5};

  //////////////////////////////////////
  void Configure(
    const gz::sim::Entity &,
    const std::shared_ptr<const sdf::Element> &,
    gz::sim::EntityComponentManager &,
    gz::sim::EventManager &) override
  {
    std::cout << "[ConveyorPlugin] RUNNING" << std::endl;
  }

  //////////////////////////////////////
  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    ecm.Each<gz::sim::components::Link>(
      [&](const gz::sim::Entity &entity,
          const gz::sim::components::Link *) -> bool
      {
        // aplicar velocidad (simula cinta)
        ecm.CreateComponent(
          entity,
          gz::sim::components::LinearVelocity({0, this->velocity, 0})
        );

        return true;
      });
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)