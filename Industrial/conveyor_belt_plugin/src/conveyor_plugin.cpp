#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Joint.hh>
#include <gz/sim/components/JointVelocityCmd.hh>
#include <gz/plugin/Register.hh>

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

  //////////////////////////////////////
  void Configure(
    const gz::sim::Entity &entity,
    const std::shared_ptr<const sdf::Element> &,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);

    this->joint = this->model.JointByName(ecm, "belt_joint");

    if (this->joint == gz::sim::kNullEntity)
    {
      std::cout << "Joint NOT FOUND\n";
      return;
    }

    std::cout << "Conveyor READY\n";
  }

  //////////////////////////////////////
  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    if (this->joint == gz::sim::kNullEntity)
      return;

    auto vel = ecm.Component<gz::sim::components::JointVelocityCmd>(this->joint);

    if (!vel)
    {
      ecm.CreateComponent(
        this->joint,
        gz::sim::components::JointVelocityCmd({this->velocity})
      );
    }
    else
    {
      vel->Data()[0] = this->velocity;
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