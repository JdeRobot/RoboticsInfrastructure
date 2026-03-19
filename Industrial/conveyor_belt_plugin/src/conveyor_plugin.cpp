#include <gz/sim/System.hh>
#include <gz/plugin/Register.hh>
#include <iostream>

namespace conveyor
{

class ConveyorPlugin :
  public gz::sim::System,
  public gz::sim::ISystemConfigure
{
public:

  void Configure(
    const gz::sim::Entity &,
    const std::shared_ptr<const sdf::Element> &,
    gz::sim::EntityComponentManager &,
    gz::sim::EventManager &) override
  {
    std::cout << "[ConveyorPlugin] Loaded correctly" << std::endl;
  }

};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure
)