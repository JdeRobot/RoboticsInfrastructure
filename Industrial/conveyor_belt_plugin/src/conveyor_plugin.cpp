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
  double velocity{0.2};

  void Configure(
    const gz::sim::Entity &entity,
    const std::shared_ptr<const sdf::Element> &sdf,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);

    std::string jointName = sdf->Get<std::string>("joint_name");
    this->velocity = sdf->Get<double>("velocity");

    auto jointEntity = this->model.JointByName(ecm, jointName);
    this->joint = gz::sim::Joint(jointEntity);

    std::cout << "[ConveyorPlugin] Using joint: " << jointName << std::endl;
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    if (!this->link.Valid(ecm))
      return;

    this->link.SetLinearVelocity(ecm, {0, this->velocity, 0});
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)