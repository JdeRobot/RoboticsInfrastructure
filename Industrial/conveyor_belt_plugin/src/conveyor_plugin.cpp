#include <gz/sim/System.hh>
#include <gz/sim/components/JointForceCmd.hh>
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
    std::cout << "\n[Conveyor][INIT] Configuring plugin...\n";

    if (_sdf->HasElement("velocity"))
      velocity_ = _sdf->Get<double>("velocity");

    if (_sdf->HasElement("debug"))
      debug_ = _sdf->Get<bool>("debug");

    std::cout << "[Conveyor][INIT] velocity: " << velocity_ << std::endl;
    std::cout << "[Conveyor][INIT] debug: " << debug_ << std::endl;

    _ecm.Each<gz::sim::components::Name>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Name *_name)->bool
      {
        if (_name->Data() == "belt_joint")
        {
          joint_ = _entity;

          std::cout << "[Conveyor][OK] Joint encontrado: belt_joint\n";
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
      const gz::sim::UpdateInfo &_info,
      gz::sim::EntityComponentManager &_ecm) override
  {
    if (_info.paused)
      return;

    if (joint_ == gz::sim::kNullEntity)
    {
      std::cerr << "[Conveyor][ERROR] Joint inválido en PreUpdate\n";
      return;
    }

    auto posComp =
      _ecm.Component<gz::sim::components::JointPosition>(joint_);

    if (!posComp)
    {
      std::cerr << "[Conveyor][WARN] JointPosition no disponible\n";
    }
    else if (debug_)
    {
      double pos = posComp->Data()[0];
      std::cout << "[Conveyor][DEBUG] Posición joint: " << pos << std::endl;
    }

    double force = velocity_ * 50.0;

    auto forceComp =
      _ecm.Component<gz::sim::components::JointForceCmd>(joint_);

    if (!forceComp)
    {
      if (debug_)
        std::cout << "[Conveyor][DEBUG] Creando JointForceCmd\n";

      _ecm.CreateComponent(
        joint_,
        gz::sim::components::JointForceCmd({force}));
    }
    else
    {
      forceComp->Data()[0] = force;
    }

    if (debug_)
    {
      std::cout << "[Conveyor][DEBUG] Fuerza aplicada: " << force << std::endl;
    }

    if (posComp)
    {
      double pos = posComp->Data()[0];

      if (pos > 0.019)
      {
        std::cout << "[Conveyor][DEBUG] Reset posición belt\n";

        _ecm.SetComponentData<gz::sim::components::JointPosition>(
          joint_, {0.0});
      }
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