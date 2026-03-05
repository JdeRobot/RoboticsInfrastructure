#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/components/LinearVelocity.hh>
#include <gz/math/Vector3.hh>

using namespace gz;
using namespace sim;

class PersonPlugin:
  public System,
  public ISystemConfigure,
  public ISystemPreUpdate
{
  Entity modelEntity{kNullEntity};

  public: void Configure(
      const Entity &_entity,
      const std::shared_ptr<const sdf::Element> &,
      EntityComponentManager &_ecm,
      EventManager &) override
  {
      modelEntity = _entity;

      // Crear el componente si no existe
      if (!_ecm.Component<components::LinearVelocity>(modelEntity))
      {
          _ecm.CreateComponent(
              modelEntity,
              components::LinearVelocity(math::Vector3d(0,0,0)));
      }
  }

  public: void PreUpdate(
      const UpdateInfo &,
      EntityComponentManager &_ecm) override
  {
      auto vel = _ecm.Component<components::LinearVelocity>(modelEntity);

      if (vel)
      {
          vel->Data() = math::Vector3d(0.5, 0, 0);
      }
  }
};

GZ_ADD_PLUGIN(
  PersonPlugin,
  gz::sim::System,
  PersonPlugin::ISystemConfigure,
  PersonPlugin::ISystemPreUpdate
)