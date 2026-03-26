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

  double velocity{0.2};

  double minX{-0.3}, maxX{0.3};
  double minY{-0.7}, maxY{0.7};
  double beltZ{0.75};
  double tol{0.1};

  void Configure(
    const ::gz::sim::Entity &,
    const std::shared_ptr<const sdf::Element> &_sdf,
    ::gz::sim::EntityComponentManager &,
    ::gz::sim::EventManager &) override
  {
    if (_sdf && _sdf->HasElement("velocity"))
      this->velocity = _sdf->Get<double>("velocity");

    std::cout << "[ConveyorSurface] READY\n";
  }

  void PreUpdate(
    const ::gz::sim::UpdateInfo &,
    ::gz::sim::EntityComponentManager &ecm) override
  {
    ecm.Each<
      ::gz::sim::components::Name,
      ::gz::sim::components::WorldPose>(
      [&](const ::gz::sim::Entity &_entity,
          const ::gz::sim::components::Name *_name,
          const ::gz::sim::components::WorldPose *_pose)
      {
        const std::string &n = _name->Data();

        if (n.find("box") == std::string::npos)
          return true;

        auto p = _pose->Data().Pos();

        if (p.X() < minX || p.X() > maxX ||
            p.Y() < minY || p.Y() > maxY)
          return true;

        if (std::abs(p.Z() - beltZ) > tol)
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