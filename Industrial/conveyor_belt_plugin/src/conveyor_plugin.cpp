#include <gz/sim/System.hh>
#include <gz/sim/Entity.hh>

#include <gz/sim/components/Joint.hh>
#include <gz/sim/components/JointForceCmd.hh>
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

  double force{5.0};
  
  void Configure(
    const gz::sim::Entity &,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    if (_sdf && _sdf->HasElement("force"))
      force = _sdf->Get<double>("force");

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
      std::cout << "[ERROR] No se encontró belt_joint\n";
    }
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager &ecm) override
  {
    if (_info.paused)
      return;

    if (jointEntity == gz::sim::kNullEntity)
      return;

    auto forceComp =
      ecm.Component<gz::sim::components::JointForceCmd>(jointEntity);

    if (!forceComp)
    {
      ecm.CreateComponent(
        jointEntity,
        gz::sim::components::JointForceCmd({force}));
    }
    else
    {
      forceComp->Data()[0] = force;
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