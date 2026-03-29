#include <gz/sim/System.hh>
#include <gz/sim/components/JointVelocityCmd.hh>
#include <gz/sim/components/JointPosition.hh>
#include <gz/sim/components/Name.hh>

#include <gz/plugin/Register.hh>

#include <iostream>

namespace conveyor
{

class ConveyorSystem:
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  double velocity_{0.2};
  bool debug_{true};

  gz::sim::Entity joint_{gz::sim::kNullEntity};

  void Configure(
      const gz::sim::Entity &/*_entity*/,
      const std::shared_ptr<const sdf::Element> &_sdf,
      gz::sim::EntityComponentManager &_ecm,
      gz::sim::EventManager &/*_eventMgr*/) override
  {
    if (_sdf->HasElement("velocity"))
      velocity_ = _sdf->Get<double>("velocity");

    if (_sdf->HasElement("debug"))
      debug_ = _sdf->Get<bool>("debug");

    _ecm.Each<gz::sim::components::Name>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Name *_name)->bool
      {
        if (_name->Data() == "belt_joint")
        {
          joint_ = _entity;

          if (debug_)
            std::cout << "[Conveyor][OK] Joint encontrado\n";

          return false;
        }
        return true;
      });

    if (joint_ == gz::sim::kNullEntity)
    {
      std::cerr << "[Conveyor][ERROR] Joint NO encontrado\n";
    }
  }

  void PreUpdate(
      const gz::sim::UpdateInfo &/*_info*/,
      gz::sim::EntityComponentManager &_ecm) override
  {
    if (joint_ == gz::sim::kNullEntity)
      return;

    auto velComp =
      _ecm.Component<gz::sim::components::JointVelocityCmd>(joint_);

    if (!velComp)
    {
      _ecm.CreateComponent(
        joint_,
        gz::sim::components::JointVelocityCmd({velocity_}));
    }
    else
    {
      velComp->Data()[0] = velocity_;
    }

    auto posComp =
      _ecm.Component<gz::sim::components::JointPosition>(joint_);

    if (!posComp)
      return;

    double pos = posComp->Data()[0];

    if (pos > 0.019)
    {
      if (debug_)
        std::cout << "[Conveyor][DEBUG] Reset posición belt\n";

      _ecm.SetComponentData<gz::sim::components::JointPosition>(
        joint_, {0.0});
    }
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorSystem,
  gz::sim::System,
  conveyor::ConveyorSystem::ISystemConfigure,
  conveyor::ConveyorSystem::ISystemPreUpdate
)

GZ_ADD_PLUGIN_ALIAS(conveyor::ConveyorSystem, "conveyor::ConveyorSystem")