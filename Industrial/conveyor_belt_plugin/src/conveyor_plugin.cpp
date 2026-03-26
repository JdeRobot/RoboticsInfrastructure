#include <gz/sim/System.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/LinearVelocity.hh>

#include <gz/plugin/Register.hh>

#include <gz/math/Vector3.hh>

#include <iostream>

namespace conveyor
{

class ConveyorSystem :
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  double velocity{0.3};
  std::string direction{"y"};

  double min_x{-0.5}, max_x{0.5};
  double min_y{-1.0}, max_y{1.0};
  double min_z{0.6}, max_z{1.0};

  gz::math::Vector3d dir_vec{0, 0.3, 0};

  void Configure(
    const gz::sim::Entity &,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &,
    gz::sim::EventManager &) override
  {
    if (_sdf->HasElement("velocity"))
      velocity = _sdf->Get<double>("velocity");

    if (_sdf->HasElement("direction"))
      direction = _sdf->Get<std::string>("direction");

    if (_sdf->HasElement("region"))
    {
      auto region = _sdf->FindElement("region");

      min_x = region->Get<double>("min_x");
      max_x = region->Get<double>("max_x");
      min_y = region->Get<double>("min_y");
      max_y = region->Get<double>("max_y");
      min_z = region->Get<double>("min_z");
      max_z = region->Get<double>("max_z");
    }

    if (direction == "x") dir_vec = {velocity, 0, 0};
    else if (direction == "y") dir_vec = {0, velocity, 0};
    else if (direction == "z") dir_vec = {0, 0, velocity};

    std::cout << "[Conveyor PRO] READY\n";
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    ecm.Each<
      gz::sim::components::Model,
      gz::sim::components::Pose>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Model *,
          const gz::sim::components::Pose *_pose)
      {
        auto pos = _pose->Data().Pos();

        if (pos.X() < min_x || pos.X() > max_x) return true;
        if (pos.Y() < min_y || pos.Y() > max_y) return true;
        if (pos.Z() < min_z || pos.Z() > max_z) return true;

        auto nameComp =
          ecm.Component<gz::sim::components::Name>(_entity);

        if (nameComp)
        {
          const std::string &name = nameComp->Data();

          if (name.find("box") == std::string::npos)
            return true;
        }

        auto vel =
          ecm.Component<gz::sim::components::LinearVelocity>(_entity);

        if (!vel)
        {
          ecm.CreateComponent(
            _entity,
            gz::sim::components::LinearVelocity(dir_vec));
        }
        else
        {
          vel->Data() = dir_vec;
        }

        return true;
      });
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorSystem,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)