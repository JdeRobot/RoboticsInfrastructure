#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/components/LinearVelocity.hh>
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
  gz::sim::Link belt;

  double velocity{0.5};

  //////////////////////////////////////
  void Configure(
    const gz::sim::Entity &entity,
    const std::shared_ptr<const sdf::Element> &,
    gz::sim::EntityComponentManager &ecm,
    gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);

    auto linkEntity = this->model.LinkByName(ecm, "belt");
    this->belt = gz::sim::Link(linkEntity);
  }

  //////////////////////////////////////
  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    // recorrer entidades con colisión (objetos)
    ecm.Each<gz::sim::components::Collision>(
      [&](const gz::sim::Entity &entity,
          const gz::sim::components::Collision *) -> bool
      {
        // aplicar velocidad en Y
        ecm.CreateComponent(
          entity,
          gz::sim::components::LinearVelocity({0, this->velocity, 0})
        );

        return true;
      });
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)