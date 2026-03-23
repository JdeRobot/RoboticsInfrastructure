#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Joint.hh>

#include <gz/sim/components/JointVelocityCmd.hh>
#include <gz/sim/components/JointForceCmd.hh>

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

  double velocity{0.5};

  void Configure(
    const gz::sim::Entity &entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);

    ecm.Each<gz::sim::components::Joint, gz::sim::components::Name>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Joint *,
          const gz::sim::components::Name *_name)
      {
        if (_name->Data() == "belt_joint")
        {
          this->joint = _entity;
          return false;
        }
        return true;
      });

    if (_sdf && _sdf->HasElement("velocity"))
      this->velocity = _sdf->Get<double>("velocity");

    std::cout << "Buscando joint..." << std::endl;

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
        gz::sim::components::JointVelocityCmd({this->velocity}));
    }
    else
    {
      velComp->Data()[0] = this->velocity;
    }

    auto forceComp =
      ecm.Component<gz::sim::components::JointForceCmd>(this->joint);

    if (!forceComp)
    {
      ecm.CreateComponent(
        this->joint,
        gz::sim::components::JointForceCmd({200.0}));
    }
    else
    {
      forceComp->Data()[0] = 200.0;
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