#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/AngularVelocityCmd.hh>
#include <gz/sim/components/LinearVelocityCmd.hh>
#include <gz/plugin/Register.hh>

#include <gz/math/Helpers.hh>
#include <gz/math/Pose3.hh>
#include <gz/math/Quaternion.hh>
#include <gz/math/Vector3.hh>

#include <sdf/Element.hh>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <iterator>
#include <vector>

// Moves a (non static) model along a list of timed waypoints, like the
// <script><trajectory> of an actor. Unlike actors, the model keeps its
// collisions, so other models (e.g. a drone) can land on it and be carried.
//
// The motion is applied through velocity commands instead of teleporting, so
// objects resting on the model get the right contact velocity.
//
// <plugin filename="libwaypoint_follower_harmonic.so"
//         name="waypoint_follower::WaypointFollower">
//   <loop>true</loop>
//   <waypoint><time>0.0</time><pose>-12 0 0 0 0 1.5707</pose></waypoint>
//   <waypoint><time>34.3</time><pose>12 0 0 0 0 1.5707</pose></waypoint>
// </plugin>
namespace waypoint_follower
{
struct Waypoint
{
    double time;
    gz::math::Pose3d pose;
};

class WaypointFollower :
    public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate
{
private:
    gz::sim::Model model{gz::sim::kNullEntity};
    std::vector<Waypoint> waypoints;
    bool loop{true};

    // If the model is further than this from its target it is teleported
    // instead of being driven (e.g. at startup or after a reset)
    double teleport_distance{1.0};

public:
    // ============================================
    // CONFIGURE
    // ============================================
    void Configure(const gz::sim::Entity &_entity,
                   const std::shared_ptr<const sdf::Element> &_sdf,
                   gz::sim::EntityComponentManager &_ecm,
                   gz::sim::EventManager &) override
    {
        this->model = gz::sim::Model(_entity);

        if (!this->model.Valid(_ecm))
        {
            std::cerr << "[WaypointFollower] Plugin must be attached to a model\n";
            return;
        }

        if (_sdf->HasElement("loop"))
            this->loop = _sdf->Get<bool>("loop");

        if (_sdf->HasElement("teleport_distance"))
            this->teleport_distance = _sdf->Get<double>("teleport_distance");

        for (auto wp = _sdf->FindElement("waypoint"); wp;
             wp = wp->GetNextElement("waypoint"))
        {
            this->waypoints.push_back(
                {wp->Get<double>("time"), wp->Get<gz::math::Pose3d>("pose")});
        }

        std::sort(this->waypoints.begin(), this->waypoints.end(),
                  [](const Waypoint &_a, const Waypoint &_b)
                  { return _a.time < _b.time; });

        if (this->waypoints.size() < 2)
        {
            std::cerr << "[WaypointFollower] At least 2 waypoints are needed\n";
            this->waypoints.clear();
        }
    }

    // ============================================
    // UPDATE
    // ============================================
    void PreUpdate(const gz::sim::UpdateInfo &_info,
                   gz::sim::EntityComponentManager &_ecm) override
    {
        if (_info.paused || this->waypoints.empty() ||
            !this->model.Valid(_ecm))
            return;

        const double dt = std::chrono::duration<double>(_info.dt).count();
        if (dt <= 0.0)
            return;

        // Pose the model must have at the end of this step
        const double t =
            std::chrono::duration<double>(_info.simTime).count() + dt;
        const gz::math::Pose3d target = this->PoseAt(t);
        const gz::math::Pose3d current =
            gz::sim::worldPose(this->model.Entity(), _ecm);

        if (current.Pos().Distance(target.Pos()) > this->teleport_distance)
        {
            this->model.SetWorldPoseCmd(_ecm, target);
            this->SetVelocity(_ecm, gz::math::Vector3d::Zero,
                              gz::math::Vector3d::Zero);
            return;
        }

        // World velocities that take the model from its current pose to the
        // target in one step. This also corrects any drift (gravity, contacts)
        gz::math::Vector3d lin_vel = (target.Pos() - current.Pos()) / dt;

        gz::math::Vector3d axis;
        double angle;
        (target.Rot() * current.Rot().Inverse()).AxisAngle(axis, angle);
        if (angle > GZ_PI)
            angle -= 2 * GZ_PI;
        gz::math::Vector3d ang_vel = axis * (angle / dt);

        // Physics expects model velocity commands in the model frame
        this->SetVelocity(_ecm,
                          current.Rot().RotateVectorReverse(lin_vel),
                          current.Rot().RotateVectorReverse(ang_vel));
    }

private:
    // ============================================
    // HELPERS
    // ============================================
    gz::math::Pose3d PoseAt(double _t) const
    {
        const Waypoint &first = this->waypoints.front();
        const Waypoint &last = this->waypoints.back();

        if (this->loop && last.time > 0.0)
            _t = std::fmod(_t, last.time);

        if (_t <= first.time)
            return first.pose;
        if (_t >= last.time)
            return last.pose;

        auto next = std::upper_bound(
            this->waypoints.begin(), this->waypoints.end(), _t,
            [](double _time, const Waypoint &_wp) { return _time < _wp.time; });
        auto prev = std::prev(next);

        const double alpha = (_t - prev->time) / (next->time - prev->time);

        return gz::math::Pose3d(
            prev->pose.Pos() + (next->pose.Pos() - prev->pose.Pos()) * alpha,
            gz::math::Quaterniond::Slerp(
                alpha, prev->pose.Rot(), next->pose.Rot(), true));
    }

    void SetVelocity(gz::sim::EntityComponentManager &_ecm,
                     const gz::math::Vector3d &_lin,
                     const gz::math::Vector3d &_ang)
    {
        const gz::sim::Entity entity = this->model.Entity();

        if (!_ecm.Component<gz::sim::components::LinearVelocityCmd>(entity))
            _ecm.CreateComponent(entity,
                                 gz::sim::components::LinearVelocityCmd(_lin));
        else
            _ecm.SetComponentData<gz::sim::components::LinearVelocityCmd>(
                entity, _lin);

        if (!_ecm.Component<gz::sim::components::AngularVelocityCmd>(entity))
            _ecm.CreateComponent(entity,
                                 gz::sim::components::AngularVelocityCmd(_ang));
        else
            _ecm.SetComponentData<gz::sim::components::AngularVelocityCmd>(
                entity, _ang);
    }
};
}

// ============================================
// PLUGIN REGISTRATION
// ============================================
GZ_ADD_PLUGIN(
    waypoint_follower::WaypointFollower,
    gz::sim::System,
    waypoint_follower::WaypointFollower::ISystemConfigure,
    waypoint_follower::WaypointFollower::ISystemPreUpdate
)

GZ_ADD_PLUGIN_ALIAS(waypoint_follower::WaypointFollower,
                    "waypoint_follower::WaypointFollower")
