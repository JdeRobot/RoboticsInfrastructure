#include <gz/sim/System.hh>
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

  gz::sim::Entity jointEntity{kNullEntity};

  double velocity{0.5};
  double power{100.0};

  void Configure(
    const gz::sim::Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &_ecm,
    gz::sim::EventManager &) override
  {
    std::cout << "[ConveyorJointPlugin] INIT\n";

    if (_sdf->HasElement("velocity"))
      velocity = _sdf->Get<double>("velocity");

    if (_sdf->HasElement("power"))
      power = _sdf->Get<double>("power");

    _ecm.Each<gz::sim::components::Joint,
              gz::sim::components::Name>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Joint *,
          const gz::sim::components::Name *_name)
      {
        if (_name->Data() == "belt_joint")
        {
          jointEntity = _entity;
          std::cout << "[Conveyor] Joint encontrado\n";
          return false;
        }
        return true;
      });

    if (jointEntity == kNullEntity)
    {
      std::cout << "[Conveyor] ERROR: joint no encontrado\n";
    }
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &_ecm) override
  {
    if (jointEntity == kNullEntity)
      return;

    double vel = velocity * (power / 100.0);

    auto comp =
      _ecm.Component<gz::sim::components::JointVelocityCmd>(jointEntity);

    if (!comp)
    {
      _ecm.CreateComponent(
        jointEntity,
        gz::sim::components::JointVelocityCmd({vel}));
    }
    else
    {
      comp->Data()[0] = vel;
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