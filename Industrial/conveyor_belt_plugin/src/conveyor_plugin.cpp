#include <gz/sim/System.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>

#include <gz/plugin/Register.hh>

#include <iostream>

namespace conveyor
{

class ConveyorPlugin :
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  gz::sim::Entity beltLink{gz::sim::kNullEntity};
  double velocity{0.2};

  void Configure(
    const gz::sim::Entity &,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    std::cout << "[Conveyor] Configure START\n";

    if (_sdf && _sdf->HasElement("velocity"))
      this->velocity = _sdf->Get<double>("velocity");

    ecm.Each<gz::sim::components::Name>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Name *_name)
      {
        if (_name->Data() == "belt_moving")
        {
          this->beltLink = _entity;
          std::cout << "[Conveyor] belt_moving FOUND: "
                    << _entity << std::endl;
          return false;
        }
        return true;
      });

    if (this->beltLink == gz::sim::kNullEntity)
    {
      std::cout << "[Conveyor] belt_moving NOT FOUND\n";
      return;
    }

    std::cout << "[Conveyor] READY\n";
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    if (this->beltLink == gz::sim::kNullEntity)
      return;

    auto velComp =
      ecm.Component<gz::sim::components::LinearVelocityCmd>(this->beltLink);

    if (!velComp)
    {
      ecm.CreateComponent(
        this->beltLink,
        gz::sim::components::LinearVelocityCmd(
          {0.0, this->velocity, 0.0}));
    }
    else
    {
      velComp->Data()[0] = 0.0;
      velComp->Data()[1] = this->velocity;
      velComp->Data()[2] = 0.0;
    }
  }
};



GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)