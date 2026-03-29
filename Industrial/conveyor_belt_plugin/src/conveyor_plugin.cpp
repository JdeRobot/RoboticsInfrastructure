#include <gz/sim/System.hh>
#include <gz/sim/Entity.hh>

#include <gz/sim/components/LinearVelocityCmd.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Name.hh>

#include <gz/plugin/Register.hh>
#include <gz/math/Vector3.hh>

#include <iostream>

namespace conveyor
{

class ConveyorSystem:
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  double velocity_{0.0};
  std::string direction_{"x"};

  double min_x_, max_x_;
  double min_y_, max_y_;
  double min_z_, max_z_;

  bool debug_{true};

  void Configure(
      const gz::sim::Entity &/*_entity*/,
      const std::shared_ptr<const sdf::Element> &_sdf,
      gz::sim::EntityComponentManager &/*_ecm*/,
      gz::sim::EventManager &/*_eventMgr*/) override
  {
    if (_sdf->HasElement("velocity"))
      velocity_ = _sdf->Get<double>("velocity");

    if (_sdf->HasElement("direction"))
      direction_ = _sdf->Get<std::string>("direction");

    if (_sdf->HasElement("debug"))
      debug_ = _sdf->Get<bool>("debug");

    auto region = _sdf->FindElement("region");

    if (!region)
    {
      std::cerr << "[Conveyor][ERROR] No region defined\n";
      return;
    }

    min_x_ = region->Get<double>("min_x");
    max_x_ = region->Get<double>("max_x");
    min_y_ = region->Get<double>("min_y");
    max_y_ = region->Get<double>("max_y");
    min_z_ = region->Get<double>("min_z");
    max_z_ = region->Get<double>("max_z");

    std::cout << "[Conveyor] Plugin cargado\n";
  }

  void PreUpdate(
      const gz::sim::UpdateInfo &_info,
      gz::sim::EntityComponentManager &_ecm) override
  {
    double dt = _info.dt.count() / 1e9;

    _ecm.Each<
      gz::sim::components::Pose,
      gz::sim::components::Name>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Pose *_pose,
          const gz::sim::components::Name *_name)->bool
      {
        auto pos = _pose->Data().Pos();

        bool inside =
          pos.X() > min_x_ && pos.X() < max_x_ &&
          pos.Y() > min_y_ && pos.Y() < max_y_ &&
          pos.Z() > min_z_ && pos.Z() < max_z_;

        auto velComp =
          _ecm.Component<gz::sim::components::LinearVelocityCmd>(_entity);

        gz::math::Vector3d vel =
          velComp ? velComp->Data() : gz::math::Vector3d(0,0,0);

        if (inside)
        {
          if (direction_ == "x")
            vel.X() += velocity_ * dt;

          if (direction_ == "y")
            vel.Y() += velocity_ * dt;
        }
        else
        {
          if (direction_ == "x")
            vel.X() *= 0.9;

          if (direction_ == "y")
            vel.Y() *= 0.9;
        }

        if (!velComp)
        {
          _ecm.CreateComponent(
            _entity,
            gz::sim::components::LinearVelocityCmd(vel));
        }
        else
        {
          velComp->Data() = vel;
        }

        return true;
      });
  }
};

}

GZ_ADD_PLUGIN(
  conveyor::ConveyorSystem,
  gz::sim::System,
  conveyor::ConveyorSystem::ISystemConfigure,
  conveyor::ConveyorSystem::ISystemPreUpdate
)

GZ_ADD_PLUGIN_ALIAS(conveyor::ConveyorSystem, "conveyor::ConveyorSystem")