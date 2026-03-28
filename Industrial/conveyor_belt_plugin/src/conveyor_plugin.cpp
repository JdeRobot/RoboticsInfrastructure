#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Entity.hh>
#include <gz/sim/Util.hh>

#include <gz/sim/components/LinearVelocity.hh>
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

  gz::math::Vector3d dir_vec_{0,0,0};

  gz::sim::Entity modelEntity_{gz::sim::kNullEntity};

  void Configure(
      const gz::sim::Entity &_entity,
      const std::shared_ptr<const sdf::Element> &_sdf,
      gz::sim::EntityComponentManager &/*_ecm*/,
      gz::sim::EventManager &/*_eventMgr*/) override
  {
    modelEntity_ = _entity;

    if (_sdf->HasElement("velocity"))
      velocity_ = _sdf->Get<double>("velocity");

    if (_sdf->HasElement("direction"))
      direction_ = _sdf->Get<std::string>("direction");

    auto region = _sdf->GetElement("region");

    min_x_ = region->Get<double>("min_x");
    max_x_ = region->Get<double>("max_x");
    min_y_ = region->Get<double>("min_y");
    max_y_ = region->Get<double>("max_y");
    min_z_ = region->Get<double>("min_z");
    max_z_ = region->Get<double>("max_z");

    if (direction_ == "x") dir_vec_ = {1,0,0};
    else if (direction_ == "y") dir_vec_ = {0,1,0};
    else if (direction_ == "z") dir_vec_ = {0,0,1};

    std::cout << "[Conveyor] Plugin cargado correctamente\n";
  }

  void PreUpdate(
      const gz::sim::UpdateInfo &/*_info*/,
      gz::sim::EntityComponentManager &_ecm) override
  {
    _ecm.Each<gz::sim::components::Pose>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Pose *_pose)->bool
      {
        auto pos = _pose->Data().Pos();

        if (pos.X() > min_x_ && pos.X() < max_x_ &&
            pos.Y() > min_y_ && pos.Y() < max_y_ &&
            pos.Z() > min_z_ && pos.Z() < max_z_)
        {
          auto velComp =
            _ecm.Component<gz::sim::components::LinearVelocity>(_entity);

          if (!velComp)
          {
            _ecm.CreateComponent(
              _entity,
              gz::sim::components::LinearVelocity(
                dir_vec_ * velocity_));
          }
          else
          {
            velComp->Data() = dir_vec_ * velocity_;
          }
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