#include <gz/sim/System.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>
#include <gz/sim/components/LinearVelocity.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/CanonicalLink.hh>

#include <gz/plugin/Register.hh>

#include <iostream>
#include <string>

namespace conveyor
{

class ConveyorSurfacePlugin :
  public ::gz::sim::System,
  public ::gz::sim::ISystemConfigure,
  public ::gz::sim::ISystemPreUpdate
{
public:

  double velocity{0.1};

  double minX{-0.25}, maxX{0.25};
  double minY{-0.6},  maxY{0.6};
  double beltZ{0.75};
  double zTolerance{0.05}; 

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
    ecm.Each<::gz::sim::components::Name,
             ::gz::sim::components::WorldPose>(
      [&](const ::gz::sim::Entity &_entity,
          const ::gz::sim::components::Name *_name,
          const ::gz::sim::components::WorldPose *_pose)
      {
        const std::string &n = _name->Data();

        if (n.find("box") == std::string::npos)
          return true;

        const auto &p = _pose->Data().Pos();

        if (p.X() < minX || p.X() > maxX ||
            p.Y() < minY || p.Y() > maxY)
          return true;

        if (std::abs(p.Z() - beltZ) > zTolerance)
          return true;

        auto velCmd =
          ecm.Component<::gz::sim::components::LinearVelocityCmd>(_entity);

        if (!velCmd)
        {
          ecm.CreateComponent(
            _entity,
            ::gz::sim::components::LinearVelocityCmd(
              {0.0, this->velocity, 0.0}));
        }
        else
        {
          velCmd->Data()[0] = 0.0;
          velCmd->Data()[1] = this->velocity;
          velCmd->Data()[2] = 0.0;
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