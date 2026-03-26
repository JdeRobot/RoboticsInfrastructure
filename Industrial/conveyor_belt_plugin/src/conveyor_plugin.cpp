#include <gz/sim/System.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>

#include <gz/plugin/Register.hh>

#include <iostream>

namespace conveyor
{

class ConveyorSurfacePlugin :
  public ::gz::sim::System,
  public ::gz::sim::ISystemConfigure,
  public ::gz::sim::ISystemPreUpdate
{
public:

  double velocity{0.3};

  void Configure(
    const ::gz::sim::Entity &,
    const std::shared_ptr<const sdf::Element> &_sdf,
    ::gz::sim::EntityComponentManager &,
    ::gz::sim::EventManager &) override
  {
    if (_sdf && _sdf->HasElement("velocity"))
      velocity = _sdf->Get<double>("velocity");

    std::cout << "[Conveyor] READY\n";
  }

  void PreUpdate(
    const ::gz::sim::UpdateInfo &,
    ::gz::sim::EntityComponentManager &ecm) override
  {
    ecm.Each<
      ::gz::sim::components::Name,
      ::gz::sim::components::Pose>(
      [&](const ::gz::sim::Entity &_entity,
          const ::gz::sim::components::Name *_name,
          const ::gz::sim::components::Pose *_pose)
      {
        const std::string &name = _name->Data();

        // Solo cajas
        if (name.find("box") == std::string::npos)
          return true;

        auto p = _pose->Data().Pos();

        // Zona de la cinta
        if (p.Z() < 0.7 || p.Z() > 0.9)
          return true;

        if (p.X() < -0.3 || p.X() > 0.3)
          return true;

        if (p.Y() < -0.7 || p.Y() > 0.7)
          return true;

        auto vel =
          ecm.Component<::gz::sim::components::LinearVelocityCmd>(_entity);

        if (!vel)
        {
          ecm.CreateComponent(
            _entity,
            ::gz::sim::components::LinearVelocityCmd(
              {0.0, velocity, 0.0}));
        }
        else
        {
          vel->Data()[1] = velocity;
        }

        return true;
      });
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorSurfacePlugin,
  ::gz::sim::System,
  ::gz::sim::ISystemConfigure,
  ::gz::sim::ISystemPreUpdate
)