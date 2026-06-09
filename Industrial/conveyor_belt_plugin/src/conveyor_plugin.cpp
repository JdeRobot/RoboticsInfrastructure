#include <gz/sim/System.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Link.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/ExternalWorldWrenchCmd.hh>
#include <gz/sim/components/LinearVelocity.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>

#include <gz/plugin/Register.hh>
#include <gz/math/Vector3.hh>
#include <gz/msgs/wrench.pb.h>

namespace box_mover
{

class BoxMoverPlugin:
  public gz::sim::System,
  public gz::sim::ISystemPreUpdate
{
public:

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &_ecm) override
  {
    _ecm.Each<
      gz::sim::components::Model,
      gz::sim::components::Name,
      gz::sim::components::Pose>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Model *,
          const gz::sim::components::Name *_name,
          const gz::sim::components::Pose *_pose)->bool
      {
        std::string name = _name->Data();

        if (name.find("box_") == std::string::npos)
          return true;

        auto pos = _pose->Data().Pos();

        // Eliminar salchichas que han caído al suelo
        if (pos.Z() < 0.1)
        {
          _ecm.RequestRemoveEntity(_entity);
          return true;
        }

        bool inside =
          pos.X() > -0.25 && pos.X() < 0.25 &&
          pos.Y() > -0.6  && pos.Y() < 0.6 &&
          pos.Z() > 0.6 && pos.Z() < 0.90;

        auto links = _ecm.ChildrenByComponents(
          _entity, gz::sim::components::Link());

        for (auto link : links)
        {
          if (inside)
          {
            ApplyForce(_ecm, link);
            StabilizeMotion(_ecm, link);
          }
        }

        return true;
      });
  }

  void ApplyForce(
    gz::sim::EntityComponentManager &_ecm,
    gz::sim::Entity entity)
  {
    gz::math::Vector3d force(0, -0.5, 0);

    gz::msgs::Wrench wrenchMsg;

    wrenchMsg.mutable_force()->set_x(force.X());
    wrenchMsg.mutable_force()->set_y(force.Y());
    wrenchMsg.mutable_force()->set_z(0);

    wrenchMsg.mutable_torque()->set_x(0);
    wrenchMsg.mutable_torque()->set_y(0);
    wrenchMsg.mutable_torque()->set_z(0);

    auto comp =
      _ecm.Component<gz::sim::components::ExternalWorldWrenchCmd>(entity);

    if (!comp)
    {
      _ecm.CreateComponent(
        entity,
        gz::sim::components::ExternalWorldWrenchCmd(wrenchMsg));
    }
    else
    {
      comp->Data() = wrenchMsg;
    }
  }

  void StabilizeMotion(
    gz::sim::EntityComponentManager &_ecm,
    gz::sim::Entity entity)
  {
    auto velComp =
      _ecm.Component<gz::sim::components::LinearVelocity>(entity);

    if (!velComp)
      return;

    auto vel = velComp->Data();

    vel.X() = 0;

    auto cmdComp =
      _ecm.Component<gz::sim::components::LinearVelocityCmd>(entity);

    if (!cmdComp)
    {
      _ecm.CreateComponent(
        entity,
        gz::sim::components::LinearVelocityCmd(vel));
    }
    else
    {
      cmdComp->Data() = vel;
    }
  }
};

}

GZ_ADD_PLUGIN(
  box_mover::BoxMoverPlugin,
  gz::sim::System,
  box_mover::BoxMoverPlugin::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(box_mover::BoxMoverPlugin, "box_mover::BoxMoverPlugin")