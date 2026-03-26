#include <gz/sim/System.hh>
#include <gz/sim/Entity.hh>
#include <gz/sim/components/Joint.hh>
#include <gz/sim/components/JointVelocityCmd.hh>
#include <gz/sim/components/Name.hh>

#include <gz/plugin/Register.hh>

#include <iostream>

namespace conveyor
{

class ConveyorJointPlugin :
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  gz::sim::Entity jointEntity{gz::sim::kNullEntity};

  double velocity{0.3};

  void Configure(
    const gz::sim::Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    if (_sdf && _sdf->HasElement("velocity"))
      velocity = _sdf->Get<double>("velocity");

    ecm.Each<gz::sim::components::Joint,
             gz::sim::components::Name>(
      [&](const gz::sim::Entity &_ent,
          const gz::sim::components::Joint *,
          const gz::sim::components::Name *_name)
      {
        if (_name->Data() == "belt_joint")
        {
          jointEntity = _ent;
          std::cout << "[Conveyor] Joint encontrado\n";
          return false;
        }
        return true;
      });

    if (jointEntity == gz::sim::kNullEntity)
    {
      std::cout << "[Conveyor ERROR] No se encontró belt_joint\n";
    }
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    if (jointEntity == gz::sim::kNullEntity)
      return;

    auto velComp =
      ecm.Component<gz::sim::components::JointVelocityCmd>(jointEntity);

    if (!velComp)
    {
      ecm.CreateComponent(
        jointEntity,
        gz::sim::components::JointVelocityCmd({velocity}));
    }
    else
    {
      velComp->Data()[0] = velocity;
    }
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorJointPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)