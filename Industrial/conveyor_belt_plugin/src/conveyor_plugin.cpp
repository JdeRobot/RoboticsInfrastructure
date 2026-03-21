#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
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
  gz::sim::Link link{gz::sim::kNullEntity};
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

    auto linkEntity = this->model.LinkByName(ecm, linkName);
    this->link = gz::sim::Link(linkEntity);

    std::cout << "[ConveyorPlugin] Loaded, link: " << linkName << std::endl;
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &) override
  {
    if (!this->link.Valid())
      return;

    // 🔥 ESTA ES LA CLAVE
    this->link.SetLinearVel({0, this->velocity, 0});
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)