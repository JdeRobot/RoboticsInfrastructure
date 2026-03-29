#include <gz/sim/System.hh>
#include <gz/sim/Entity.hh>

#include <gz/sim/components/ExternalWorldWrenchCmd.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Link.hh>

#include <gz/plugin/Register.hh>
#include <gz/math/Vector3.hh>
#include <gz/msgs/wrench.pb.h>

namespace conveyor
{

class ConveyorSystem:
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  double force_{5.0};
  std::string direction_{"y"};

  double min_x_, max_x_;
  double min_y_, max_y_;
  double min_z_, max_z_;

  gz::math::Vector3d dir_vec_{0,0,0};

  void Configure(
      const gz::sim::Entity &/*_entity*/,
      const std::shared_ptr<const sdf::Element> &_sdf,
      gz::sim::EntityComponentManager &/*_ecm*/,
      gz::sim::EventManager &/*_eventMgr*/) override
  {
    double velocity = _sdf->Get<double>("velocity");

    force_ = velocity * 15.0;

    direction_ = _sdf->Get<std::string>("direction");

    auto region = _sdf->FindElement("region");

    min_x_ = region->Get<double>("min_x");
    max_x_ = region->Get<double>("max_x");
    min_y_ = region->Get<double>("min_y");
    max_y_ = region->Get<double>("max_y");
    min_z_ = region->Get<double>("min_z");
    max_z_ = region->Get<double>("max_z");

    if (direction_ == "x") dir_vec_ = {1,0,0};
    else if (direction_ == "y") dir_vec_ = {0,1,0};
  }

  void PreUpdate(
      const gz::sim::UpdateInfo &/*_info*/,
      gz::sim::EntityComponentManager &_ecm) override
  {
    _ecm.Each<
      gz::sim::components::Pose,
      gz::sim::components::Link>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Pose *_pose,
          const gz::sim::components::Link *)->bool
      {
        auto pos = _pose->Data().Pos();

        bool inside =
          pos.X() > min_x_ && pos.X() < max_x_ &&
          pos.Y() > min_y_ && pos.Y() < max_y_ &&
          pos.Z() > min_z_ && pos.Z() < max_z_;

        if (inside)
        {
          gz::msgs::Wrench wrench;

          wrench.mutable_force()->set_x(dir_vec_.X() * force_);
          wrench.mutable_force()->set_y(dir_vec_.Y() * force_);
          wrench.mutable_force()->set_z(0);

          auto wrenchComp =
            _ecm.Component<gz::sim::components::ExternalWorldWrenchCmd>(_entity);

          if (!wrenchComp)
          {
            _ecm.CreateComponent(
              _entity,
              gz::sim::components::ExternalWorldWrenchCmd(wrench));
          }
          else
          {
            wrenchComp->Data() = wrench;
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