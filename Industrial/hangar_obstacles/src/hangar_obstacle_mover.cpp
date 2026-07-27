#include <cmath>
#include <string>

#include <gz/sim/System.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/components/Link.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>
#include <gz/sim/components/AngularVelocityCmd.hh>

#include <gz/plugin/Register.hh>
#include <gz/math/Vector3.hh>
#include <gz/math/Pose3.hh>

using namespace gz;
using namespace sim;

namespace hangar_obstacles
{

// Generic mover for hangar obstacles: either oscillates back and forth along
// an axis (sinusoidal position) or spins continuously around an axis. Every
// instance sets its own <mode>/<axis>/<amplitude>/<period> via the
// per-<include> <plugin> block, so the same model geometry (a panel, an
// X-shaped blade, ...) can be reused at different positions/speeds.
//
// Obstacle models must be <static>false</static> with gravity disabled on
// their link: velocity commands only move non-static (dynamic) links, and
// only dynamic bodies get their collisions re-checked against the drone
// every physics step - a "static" body's visual pose can be moved directly,
// but its collision stays frozen at load time (confirmed experimentally).
//
// Motion is feedforward (the derivative of the intended trajectory) plus a
// proportional correction back to that trajectory, so a drone bumping into
// an obstacle can't permanently knock it off its programmed path.
class ObstacleMover:
  public System,
  public ISystemConfigure,
  public ISystemPreUpdate
{
public:
  void Configure(
    const Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    EntityComponentManager &_ecm,
    EventManager &) override
  {
    modelEntity = _entity;

    if (_sdf->HasElement("mode"))
      mode = _sdf->Get<std::string>("mode");

    if (_sdf->HasElement("axis"))
      axis = _sdf->Get<gz::math::Vector3d>("axis");
    axis = axis.Normalized();

    if (_sdf->HasElement("amplitude"))
      amplitude = _sdf->Get<double>("amplitude");

    if (_sdf->HasElement("period"))
      period = _sdf->Get<double>("period");

    auto links = _ecm.ChildrenByComponents(modelEntity, components::Link());
    if (!links.empty())
      linkEntity = links[0];

    auto poseComp = _ecm.Component<components::Pose>(modelEntity);
    if (poseComp)
      initialPose = poseComp->Data();
  }

  void PreUpdate(
    const UpdateInfo &_info,
    EntityComponentManager &_ecm) override
  {
    if (_info.paused || period <= 0.0 || linkEntity == kNullEntity)
      return;

    double t = std::chrono::duration<double>(_info.simTime).count();
    double omega = 2.0 * M_PI / period;
    double phase = omega * t;

    auto poseComp = _ecm.Component<components::Pose>(modelEntity);
    gz::math::Pose3d current = poseComp ? poseComp->Data() : initialPose;

    constexpr double kP = 20.0;

    if (mode == "rotate")
    {
      // Hold position at the mount point; spin freely around axis.
      gz::math::Vector3d posError = initialPose.Pos() - current.Pos();
      SetLinear(_ecm, current.Rot().RotateVectorReverse(posError * kP));
      SetAngular(_ecm, current.Rot().RotateVectorReverse(axis * omega));
    }
    else
    {
      gz::math::Vector3d target =
        initialPose.Pos() + axis * (amplitude * std::sin(phase));
      gz::math::Vector3d feedforward =
        axis * (amplitude * omega * std::cos(phase));
      gz::math::Vector3d posError = target - current.Pos();

      SetLinear(_ecm, current.Rot().RotateVectorReverse(feedforward + posError * kP));
      // Cancel any spin picked up from a collision impact.
      SetAngular(_ecm, gz::math::Vector3d::Zero);
    }
  }

private:
  void SetLinear(EntityComponentManager &_ecm, const gz::math::Vector3d &_vel)
  {
    auto comp = _ecm.Component<components::LinearVelocityCmd>(linkEntity);
    if (!comp)
      _ecm.CreateComponent(linkEntity, components::LinearVelocityCmd(_vel));
    else
      comp->Data() = _vel;
  }

  void SetAngular(EntityComponentManager &_ecm, const gz::math::Vector3d &_vel)
  {
    auto comp = _ecm.Component<components::AngularVelocityCmd>(linkEntity);
    if (!comp)
      _ecm.CreateComponent(linkEntity, components::AngularVelocityCmd(_vel));
    else
      comp->Data() = _vel;
  }

  Entity modelEntity{kNullEntity};
  Entity linkEntity{kNullEntity};

  std::string mode{"oscillate"};
  gz::math::Vector3d axis{1, 0, 0};
  double amplitude{1.0};
  double period{4.0};

  gz::math::Pose3d initialPose;
};

}  // namespace hangar_obstacles

GZ_ADD_PLUGIN(
  hangar_obstacles::ObstacleMover,
  gz::sim::System,
  hangar_obstacles::ObstacleMover::ISystemConfigure,
  hangar_obstacles::ObstacleMover::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(hangar_obstacles::ObstacleMover, "hangar_obstacles::ObstacleMover")
