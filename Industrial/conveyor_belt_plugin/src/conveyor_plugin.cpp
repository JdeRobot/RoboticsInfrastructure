#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Joint.hh>
#include <gz/sim/components/JointVelocityCmd.hh>
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
  gz::sim::Entity joint{gz::sim::kNullEntity};

  double velocity{0.3};

  void Configure(
    const gz::sim::Entity &entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);

    this->joint = this->model.JointByName(ecm, "belt_joint");

    if (_sdf && _sdf->HasElement("velocity"))
      this->velocity = _sdf->Get<double>("velocity");

    if (this->joint == gz::sim::kNullEntity)
    {
      std::cout << "Joint NOT FOUND\n";
      return;
    }

    std::cout << "Conveyor READY\n";
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    if (this->joint == gz::sim::kNullEntity)
      return;

    auto velComp =
      ecm.Component<gz::sim::components::JointVelocityCmd>(this->joint);

    if (!velComp)
    {
      ecm.CreateComponent(
        this->joint,
        gz::sim::components::JointVelocityCmd({this->velocity})
      );
    }
    else
    {
      velComp->Data()[0] = this->velocity;
    }

    // DEBUG
    std::cout << "VEL: " << this->velocity << std::endl;
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)