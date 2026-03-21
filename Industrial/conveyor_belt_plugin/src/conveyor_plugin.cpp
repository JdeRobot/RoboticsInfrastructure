#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Util.hh>
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
  gz::sim::Entity linkEntity{gz::sim::kNullEntity};
  double velocity{0.2};

  void Configure(
    const gz::sim::Entity &entity,
    const std::shared_ptr<const sdf::Element> &sdf,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);

    std::string linkName = sdf->Get<std::string>("link_name");
    this->velocity = sdf->Get<double>("velocity");

    this->linkEntity = this->model.LinkByName(ecm, linkName);

    std::cout << "[ConveyorPlugin] Loaded, link: " << linkName << std::endl;
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    if (this->linkEntity == gz::sim::kNullEntity)
      return;

    auto velComp =
      ecm.Component<gz::sim::components::LinearVelocity>(this->linkEntity);

    if (!velComp)
    {
      ecm.CreateComponent(
        this->linkEntity,
        gz::sim::components::LinearVelocity({0, this->velocity, 0}));
    }
    else
    {
      velComp->Data() = {0, this->velocity, 0};
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