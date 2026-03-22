#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Joint.hh>
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
  gz::sim::Joint joint{gz::sim::kNullEntity};

  double velocity{0.5};

  //////////////////////////////////////
  void Configure(
    const gz::sim::Entity &entity,
    const std::shared_ptr<const sdf::Element> &,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);

    auto jointEntity = this->model.JointByName(ecm, "belt_joint");

    this->joint = gz::sim::Joint(jointEntity);

    std::cout << "[ConveyorPlugin] READY" << std::endl;
  }

  //////////////////////////////////////
  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    if (!this->joint.Valid(ecm))
      return;

    this->joint.SetVelocity(ecm, {this->velocity});
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)