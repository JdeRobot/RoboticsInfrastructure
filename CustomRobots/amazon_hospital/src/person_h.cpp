#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/plugin/Register.hh>
#include <ignition/math/Vector3.hh>
#include <ignition/math/Quaternion.hh>

#include <vector>
#include <cmath>

using namespace gz;
using namespace sim;

class PersonController :
  public System,
  public ISystemConfigure,
  public ISystemPreUpdate
{
  private:

  Model model;

  std::vector<ignition::math::Vector2d> waypoints;

  int current_wp = 0;

  double linear_speed = 0.6;
  double angular_speed = 1.5;

  public:

  void Configure(
    const Entity &_entity,
    const std::shared_ptr<const sdf::Element> &,
    EntityComponentManager &,
    EventManager &) override
  {
    this->model = Model(_entity);

    waypoints = {
      {4,6},
      {5,3},
      {5,-14.5},
      {-5,-14.5},
      {-5,-25},
      {5,-25},
      {5,-14.5},
      {-5,-14.5},
      {-5,-1},
      {-4,2},
      {-4,5},
      {-2.5,13},
      {3,13},
      {4,10}
    };
  }

  void PreUpdate(
    const UpdateInfo &_info,
    EntityComponentManager &_ecm) override
  {

    auto poseComp =
      _ecm.Component<components::Pose>(this->model.Entity());

    if (!poseComp)
      return;

    auto pose = poseComp->Data();

    auto pos = pose.Pos();
    auto yaw = pose.Rot().Yaw();

    auto target = waypoints[current_wp];

    double dx = target.X() - pos.X();
    double dy = target.Y() - pos.Y();

    double distance = std::sqrt(dx*dx + dy*dy);

    double target_yaw = std::atan2(dy, dx);

    double yaw_error = target_yaw - yaw;

    while (yaw_error > M_PI) yaw_error -= 2*M_PI;
    while (yaw_error < -M_PI) yaw_error += 2*M_PI;

    double dt = std::chrono::duration<double>(_info.dt).count();

    // rotate
    if (std::abs(yaw_error) > 0.1)
    {
      yaw += angular_speed * (yaw_error > 0 ? 1 : -1) * dt;
    }
    else
    {
      // move forward
      pos.X() += linear_speed * std::cos(yaw) * dt;
      pos.Y() += linear_speed * std::sin(yaw) * dt;
    }

    pose.Pos() = pos;
    pose.Rot() = ignition::math::Quaterniond(0,0,yaw);

    _ecm.SetComponentData<components::Pose>(
      this->model.Entity(), pose);

    // waypoint reached
    if (distance < 0.3)
    {
      current_wp = (current_wp + 1) % waypoints.size();
    }
  }
};

GZ_ADD_PLUGIN(
  PersonController,
  System,
  PersonController::ISystemConfigure,
  PersonController::ISystemPreUpdate
)