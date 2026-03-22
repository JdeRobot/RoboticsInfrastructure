#include <gz/sim/System.hh>
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
    ecm.Each<gz::sim::components::LinearVelocity>(
      [&](const gz::sim::Entity &entity,
          gz::sim::components::LinearVelocity *vel) -> bool
      {
        if (vel)
        {
          vel->Data() = {0, this->velocity, 0};
        }
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