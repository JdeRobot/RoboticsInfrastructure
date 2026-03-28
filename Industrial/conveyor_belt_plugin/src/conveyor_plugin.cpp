#include <gz/sim/System.hh>
#include <gz/sim/Entity.hh>

#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ExternalWorldWrenchCmd.hh>

#include <gz/plugin/Register.hh>
#include <gz/math/Vector3.hh>
#include <gz/msgs/wrench.pb.h>

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

  bool debug_{false};

  void Configure(
      const gz::sim::Entity &/*_entity*/,
      const std::shared_ptr<const sdf::Element> &_sdf,
      gz::sim::EntityComponentManager &/*_ecm*/,
      gz::sim::EventManager &/*_eventMgr*/) override
  {
    std::cout << "[Conveyor] Configurando plugin...\n";

    if (_sdf->HasElement("velocity"))
      velocity_ = _sdf->Get<double>("velocity");

    if (_sdf->HasElement("direction"))
      direction_ = _sdf->Get<std::string>("direction");

    if (_sdf->HasElement("debug"))
      debug_ = _sdf->Get<bool>("debug");

    auto region = _sdf->FindElement("region");

    if (!region)
    {
      std::cerr << "[Conveyor][ERROR] No region definida\n";
      return;
    }

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

    if (debug_)
    {
      std::cout << "[DEBUG] velocity: " << velocity_ << "\n";
      std::cout << "[DEBUG] direction: " << direction_ << "\n";
      std::cout << "[DEBUG] region: "
                << "X(" << min_x_ << "," << max_x_ << ") "
                << "Y(" << min_y_ << "," << max_y_ << ") "
                << "Z(" << min_z_ << "," << max_z_ << ")\n";
    }
  }

  void PreUpdate(
      const gz::sim::UpdateInfo &/*_info*/,
      gz::sim::EntityComponentManager &_ecm) override
  {
    static int counter = 0;
    counter++;

    if (debug_ && counter % 300 == 0)
      std::cout << "[DEBUG] Update activo\n";

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

        auto wrenchComp =
          _ecm.Component<gz::sim::components::ExternalWorldWrenchCmd>(_entity);

        if (inside)
        {
          if (debug_ && counter % 200 == 0)
          {
            std::cout << "[Conveyor] Dentro: "
                      << _name->Data() << "\n";
          }

          gz::math::Vector3d forceVec = dir_vec_ * (velocity_ * 20.0);

          gz::msgs::Wrench wrenchMsg;
          wrenchMsg.mutable_force()->set_x(forceVec.X());
          wrenchMsg.mutable_force()->set_y(forceVec.Y());
          wrenchMsg.mutable_force()->set_z(0.0);

          wrenchMsg.mutable_torque()->set_x(0.0);
          wrenchMsg.mutable_torque()->set_y(0.0);
          wrenchMsg.mutable_torque()->set_z(0.0);

          if (!wrenchComp)
          {
            _ecm.CreateComponent(
              _entity,
              gz::sim::components::ExternalWorldWrenchCmd(wrenchMsg)
            );
          }
          else
          {
            *wrenchComp =
              gz::sim::components::ExternalWorldWrenchCmd(wrenchMsg);
          }
        }
        else
        {
          if (wrenchComp)
          {
            gz::msgs::Wrench wrenchMsg;

            wrenchMsg.mutable_force()->set_x(0.0);
            wrenchMsg.mutable_force()->set_y(0.0);
            wrenchMsg.mutable_force()->set_z(0.0);

            wrenchMsg.mutable_torque()->set_x(0.0);
            wrenchMsg.mutable_torque()->set_y(0.0);
            wrenchMsg.mutable_torque()->set_z(0.0);

            *wrenchComp =
              gz::sim::components::ExternalWorldWrenchCmd(wrenchMsg);

            if (debug_ && counter % 200 == 0)
            {
              std::cout << "[Conveyor] Fuera: "
                        << _name->Data() << "\n";
            }
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