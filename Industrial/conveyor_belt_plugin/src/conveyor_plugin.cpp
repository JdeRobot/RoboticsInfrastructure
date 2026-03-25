#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>

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

  gz::sim::Model model{gz::sim::kNullEntity};
  gz::sim::Entity beltLink{gz::sim::kNullEntity};

  double velocity{0.5};

  void Configure(
    const gz::sim::Entity &entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);

    this->beltLink = this->model.LinkByName(ecm, "belt");

    if (_sdf && _sdf->HasElement("velocity"))
      this->velocity = _sdf->Get<double>("velocity");

    if (this->beltLink == gz::sim::kNullEntity)
    {
      std::cout << "Belt link NOT FOUND\n";
      return;
    }

    std::cout << "Conveyor READY (using LinearVelocityCmd)\n";
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

}


GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)