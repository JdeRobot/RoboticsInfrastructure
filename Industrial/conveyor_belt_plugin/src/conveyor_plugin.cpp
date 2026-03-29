#include <gz/sim/System.hh>
#include <gz/sim/Entity.hh>

#include <gz/sim/components/LinearVelocityCmd.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Link.hh>

#include <gz/plugin/Register.hh>
#include <gz/math/Vector3.hh>

#include <string>

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

  void Configure(
      const gz::sim::Entity &/*_entity*/,
      const std::shared_ptr<const sdf::Element> &_sdf,
      gz::sim::EntityComponentManager &/*_ecm*/,
      gz::sim::EventManager &/*_eventMgr*/) override
  {
    velocity_ = _sdf->Get<double>("velocity");
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
      gz::sim::components::Name,
      gz::sim::components::Link>(
      [&](const gz::sim::Entity &_entity,
          const gz::sim::components::Pose *_pose,
          const gz::sim::components::Name *_name,
          const gz::sim::components::Link *)->bool
      {
        const std::string &name = _name->Data();

        if (name.find("box") == std::string::npos)
          return true;

        auto pos = _pose->Data().Pos();

        bool inside =
          pos.X() > min_x_ && pos.X() < max_x_ &&
          pos.Y() > min_y_ && pos.Y() < max_y_ &&
          pos.Z() > min_z_ && pos.Z() < max_z_;

        auto velComp =
          _ecm.Component<gz::sim::components::LinearVelocityCmd>(_entity);

        if (inside)
        {
          gz::math::Vector3d vel =
            velComp ? velComp->Data() : gz::math::Vector3d(0,0,0);

          if (direction_ == "x") vel.X() = velocity_;
          if (direction_ == "y") vel.Y() = velocity_;

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
        }

        bool remove = false;

        if (direction_ == "y" && velocity_ < 0)
          remove = pos.Y() < (min_y_ - 0.05);

        else if (direction_ == "y" && velocity_ > 0)
          remove = pos.Y() > (max_y_ + 0.05);

        else if (direction_ == "x" && velocity_ < 0)
          remove = pos.X() < (min_x_ - 0.05);

        else if (direction_ == "x" && velocity_ > 0)
          remove = pos.X() > (max_x_ + 0.05);

        if (remove)
        {
          _ecm.RequestRemoveEntity(_entity);
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