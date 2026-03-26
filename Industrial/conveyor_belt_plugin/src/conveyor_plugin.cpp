#include <gz/sim/System.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>
#include <gz/sim/components/Model.hh>

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

  gz::math::Vector3d dir_vec{0, 1, 0};

  void Configure(
    const gz::sim::Entity &,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &,
    gz::sim::EventManager &) override
  {
    if (_sdf && _sdf->HasElement("velocity"))
      velocity = _sdf->Get<double>("velocity");

    if (_sdf && _sdf->HasElement("direction"))
      direction = _sdf->Get<std::string>("direction");

    if (_sdf && _sdf->HasElement("region"))
    {
      auto region = _sdf->FindElement("region");

      if (region)
      {
        if (region->HasElement("min_x")) min_x = region->Get<double>("min_x");
        if (region->HasElement("max_x")) max_x = region->Get<double>("max_x");
        if (region->HasElement("min_y")) min_y = region->Get<double>("min_y");
        if (region->HasElement("max_y")) max_y = region->Get<double>("max_y");
        if (region->HasElement("min_z")) min_z = region->Get<double>("min_z");
        if (region->HasElement("max_z")) max_z = region->Get<double>("max_z");
      }
    }

    gz::math::Vector3d base_dir{0, 1, 0};

    if (direction == "x") base_dir = {1, 0, 0};
    else if (direction == "y") base_dir = {0, 1, 0};
    else if (direction == "z") base_dir = {0, 0, 1};

    dir_vec = base_dir * velocity;

    std::cout << "[Conveyor PRO] READY\n";
    std::cout << "Velocity: " << velocity << std::endl;
    std::cout << "Direction: " << direction << std::endl;
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &,
    gz::sim::EntityComponentManager &ecm) override
  {
    ecm.Each<
      gz::sim::components::Model,
      gz::sim::components::Pose,
      gz::sim::components::Name>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Model *,
          const gz::sim::components::Pose *_pose,
          const gz::sim::components::Name *_name)
      {
        const std::string &name = _name->Data();

        if (name.find("box") == std::string::npos)
          return true;

        auto pos = _pose->Data().Pos();

        if (pos.X() < min_x || pos.X() > max_x) return true;
        if (pos.Y() < min_y || pos.Y() > max_y) return true;
        if (pos.Z() < min_z || pos.Z() > max_z) return true;

        auto vel =
          ecm.Component<gz::sim::components::LinearVelocityCmd>(_entity);

        if (!vel)
        {
          ecm.CreateComponent(
            _entity,
            gz::sim::components::LinearVelocityCmd(dir_vec));
        }
        else
        {
          vel->SetData(
            dir_vec,
            [](const auto &, const auto &){ return false; });
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