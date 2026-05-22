#include "gz_noisy_odometry/NoisyOdometryPlugin.hpp"
#include <gz/sim/components/Pose.hh>
#include <gz/plugin/Register.hh>
#include <tf2/LinearMath/Quaternion.h>

#include <cmath>

GZ_ADD_PLUGIN(
    custom_plugins::NoisyOdometryPlugin,
    gz::sim::System,
    custom_plugins::NoisyOdometryPlugin::ISystemConfigure,
    custom_plugins::NoisyOdometryPlugin::ISystemPostUpdate)

GZ_ADD_PLUGIN_ALIAS(custom_plugins::NoisyOdometryPlugin, "custom_plugins::NoisyOdometryPlugin")

namespace custom_plugins
{
  NoisyOdometryPlugin::NoisyOdometryPlugin() {}

  double NoisyOdometryPlugin::NormalizeAngle(double _angle) const
  {
    while (_angle > M_PI) _angle -= 2.0 * M_PI;
    while (_angle < -M_PI) _angle += 2.0 * M_PI;
    return _angle;
  }

  void NoisyOdometryPlugin::Configure(const gz::sim::Entity &_entity,
                                      const std::shared_ptr<const sdf::Element> &_sdf,
                                      gz::sim::EntityComponentManager &_ecm,
                                      gz::sim::EventManager &)
  {
    model_ = gz::sim::Model(_entity);
    if (!model_.Valid(_ecm)) return;

    gaussian_noise_coeff_ = _sdf->Get<double>("gaussian_noise", 0.05).first;
    ros_topic_ = _sdf->Get<std::string>("ros_topic", "/turtlebot3/odom_noisy").first;
    gz_cmd_vel_topic_ = _sdf->Get<std::string>("gz_cmd_vel_topic", "/turtlebot3/cmd_vel").first;
    frame_id_ = _sdf->Get<std::string>("frame_id", "odom").first;
    child_frame_id_ = _sdf->Get<std::string>("child_frame_id", "base_footprint").first;

    // If the SDF does not provide the odometry motion-model coefficients
    // explicitly, derive reasonable defaults from the legacy noise parameter.
    alpha1_ = _sdf->Get<double>("alpha1", gaussian_noise_coeff_).first;
    alpha2_ = _sdf->Get<double>("alpha2", gaussian_noise_coeff_).first;
    alpha3_ = _sdf->Get<double>("alpha3", gaussian_noise_coeff_).first;
    alpha4_ = _sdf->Get<double>("alpha4", gaussian_noise_coeff_).first;

    slip_factor_           = _sdf->Get<double>("slip_factor",           0.02).first;
    block_ratio_threshold_ = _sdf->Get<double>("block_ratio_threshold", 0.15).first;
    lateral_slip_ratio_    = _sdf->Get<double>("lateral_slip_ratio",    0.20).first;

    gz_node_.Subscribe(gz_cmd_vel_topic_, &NoisyOdometryPlugin::OnCmdVel, this);

    if (!rclcpp::ok()) rclcpp::init(0, nullptr);
    ros_node_ = rclcpp::Node::make_shared("noisy_odom_node_" + model_.Name(_ecm));

    rclcpp::QoS qos(10);
    qos.transient_local();
    ros_pub_ = ros_node_->create_publisher<nav_msgs::msg::Odometry>(ros_topic_, qos);
  }

  void NoisyOdometryPlugin::OnCmdVel(const gz::msgs::Twist &_msg)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    current_v_ = _msg.linear().x();
    current_w_ = _msg.angular().z();
  }

  void NoisyOdometryPlugin::PostUpdate(const gz::sim::UpdateInfo &_info,
                                       const gz::sim::EntityComponentManager &_ecm)
  {
    if (_info.paused) return;

    auto poseComp = _ecm.Component<gz::sim::components::Pose>(model_.Entity());
    if (!poseComp) return;

    const gz::math::Pose3d current_true_pose = poseComp->Data();

    if (!initialized_)
    {
      // The noisy odometry starts aligned with the true pose only once.
      // After that, it evolves independently by integrating noisy motion
      // increments, so drift accumulates naturally over time.
      noisy_pose_internal_ = current_true_pose;
      last_true_pose_ = current_true_pose;
      last_update_time_ = _info.simTime;
      initialized_ = true;
      return;
    }

    const double dt =
      std::chrono::duration<double>(_info.simTime - last_update_time_).count();

    if (dt <= 0.0) return;
    last_update_time_ = _info.simTime;

    // Compute the true relative motion between the last and current simulator pose.
    // This gives a physically meaningful motion increment without publishing the
    // simulator pose directly.
    const gz::math::Vector3d delta_world =
      current_true_pose.Pos() - last_true_pose_.Pos();

    const double previous_true_yaw = last_true_pose_.Rot().Yaw();
    const double current_true_yaw  = current_true_pose.Rot().Yaw();

    // Express the translation increment in the previous robot frame so the
    // odometry model operates in the body frame, as usual in planar robotics.
    const gz::math::Vector3d delta_body =
      last_true_pose_.Rot().RotateVectorReverse(delta_world);

    const double trans_true = std::sqrt(
      delta_body.X() * delta_body.X() + delta_body.Y() * delta_body.Y());

    const double delta_yaw_true = NormalizeAngle(current_true_yaw - previous_true_yaw);

    double v_cmd, w_cmd;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      v_cmd = current_v_;
      w_cmd = current_w_;
    }

    // Detect whether the robot is physically blocked: a non-negligible command
    // is being sent but the simulator reports no real displacement.
    // In that case a small fraction of the commanded motion leaks into the
    // odometry, simulating wheel slip against the obstacle — exactly what real
    // encoders would observe when the wheels spin without moving the chassis.
    const double trans_cmd     = v_cmd * dt;
    const double delta_rot_cmd = w_cmd * dt;

    // Ratio-based detection: blocked when a commanded axis achieves less than
    // block_ratio_threshold_ of the expected increment. More robust than a fixed
    // absolute threshold, which can misfire on slow robots or tiny commands.
    // Single-tick detection (no hysteresis): the physics engine makes the robot
    // bounce on alternate ticks against a wall, so any multi-tick accumulator
    // would never trigger.
    const bool is_commanded    = std::abs(trans_cmd) > 1e-4 || std::abs(delta_rot_cmd) > 1e-4;
    const bool linear_stalled  = std::abs(trans_cmd)     > 1e-4 &&
                                  trans_true              < block_ratio_threshold_ * std::abs(trans_cmd);
    const bool angular_stalled = std::abs(delta_rot_cmd) > 1e-4 &&
                                  std::abs(delta_yaw_true) < block_ratio_threshold_ * std::abs(delta_rot_cmd);
    const bool is_blocked      = is_commanded && (linear_stalled || angular_stalled);

    const double trans    = is_blocked ? trans_cmd    * slip_factor_ : trans_true;
    const double delta_yaw = is_blocked ? delta_rot_cmd * slip_factor_ : delta_yaw_true;

    // When blocked, delta_body is near-zero simulator noise so atan2 returns a
    // random angle. Force rot1=0 so the slip integrates along the robot's
    // current heading, which is the only physically meaningful direction.
    const double rot1 =
      (!is_blocked && trans > 1e-9) ? NormalizeAngle(std::atan2(delta_body.Y(), delta_body.X())) : 0.0;
    const double rot2 = NormalizeAngle(delta_yaw - rot1);

    // Odometry motion model:
    //   - rotation uncertainty grows with both rotation and translation
    //   - translation uncertainty grows with both translation and turning
    //
    // This is more robust than injecting noise directly on cmd_vel, and still
    // preserves the expected long-term drift because only noisy increments are
    // integrated into the internal odometric state.
    const double sigma_rot1 =
      alpha1_ * std::abs(rot1) + alpha2_ * std::abs(trans);
    const double sigma_trans =
      alpha3_ * std::abs(trans) + alpha4_ * (std::abs(rot1) + std::abs(rot2));
    const double sigma_rot2 =
      alpha1_ * std::abs(rot2) + alpha2_ * std::abs(trans);

    const double rot1_noisy  = rot1  + gz::math::Rand::DblNormal(0.0, sigma_rot1);
    const double trans_noisy = trans + gz::math::Rand::DblNormal(0.0, sigma_trans);
    const double rot2_noisy  = rot2  + gz::math::Rand::DblNormal(0.0, sigma_rot2);

    // Integrate the noisy relative motion over the internal odometry state.
    // This is the key point that makes the estimate drift over time instead of
    // snapping back to the true simulator pose.
    const double current_noisy_yaw  = noisy_pose_internal_.Rot().Yaw();
    const double heading_after_rot1 = current_noisy_yaw + rot1_noisy;
    const double new_noisy_yaw =
      NormalizeAngle(current_noisy_yaw + rot1_noisy + rot2_noisy);

    noisy_pose_internal_.Pos().X(
      noisy_pose_internal_.Pos().X() + trans_noisy * std::cos(heading_after_rot1));
    noisy_pose_internal_.Pos().Y(
      noisy_pose_internal_.Pos().Y() + trans_noisy * std::sin(heading_after_rot1));
    noisy_pose_internal_.Pos().Z(current_true_pose.Pos().Z());

    // When blocked, wheels spinning against a wall generate small random
    // perpendicular micro-displacements (lateral slip). The direction is
    // always 90° to the heading, so it cannot reverse the longitudinal slip.
    if (is_blocked && lateral_slip_ratio_ > 0.0)
    {
      const double lateral = gz::math::Rand::DblNormal(
        0.0, std::abs(trans) * lateral_slip_ratio_);
      noisy_pose_internal_.Pos().X(
        noisy_pose_internal_.Pos().X() - lateral * std::sin(heading_after_rot1));
      noisy_pose_internal_.Pos().Y(
        noisy_pose_internal_.Pos().Y() + lateral * std::cos(heading_after_rot1));
    }

    noisy_pose_internal_.Rot() = gz::math::Quaterniond(0.0, 0.0, new_noisy_yaw);
    noisy_pose_internal_.Rot().Normalize();

    // The published twist is consistent with the noisy increment that has just
    // been integrated. This keeps the message self-consistent.
    last_noisy_linear_velocity_  = trans_noisy / dt;
    last_noisy_angular_velocity_ = NormalizeAngle(rot1_noisy + rot2_noisy) / dt;

    nav_msgs::msg::Odometry odom_msg;
    odom_msg.header.stamp = ros_node_->now();
    odom_msg.header.frame_id = frame_id_;
    odom_msg.child_frame_id = child_frame_id_;

    odom_msg.pose.pose.position.x = noisy_pose_internal_.Pos().X();
    odom_msg.pose.pose.position.y = noisy_pose_internal_.Pos().Y();
    odom_msg.pose.pose.position.z = noisy_pose_internal_.Pos().Z();

    odom_msg.pose.pose.orientation.x = noisy_pose_internal_.Rot().X();
    odom_msg.pose.pose.orientation.y = noisy_pose_internal_.Rot().Y();
    odom_msg.pose.pose.orientation.z = noisy_pose_internal_.Rot().Z();
    odom_msg.pose.pose.orientation.w = noisy_pose_internal_.Rot().W();

    odom_msg.twist.twist.linear.x = last_noisy_linear_velocity_;
    odom_msg.twist.twist.linear.y = 0.0;
    odom_msg.twist.twist.linear.z = 0.0;

    odom_msg.twist.twist.angular.x = 0.0;
    odom_msg.twist.twist.angular.y = 0.0;
    odom_msg.twist.twist.angular.z = last_noisy_angular_velocity_;

    // Fill the most relevant covariance entries with values consistent with the
    // motion model. The message remains simple, but no longer pretends to have
    // perfect certainty.
    const double pose_var_xy  = sigma_trans * sigma_trans;
    const double pose_var_yaw =
      (sigma_rot1 * sigma_rot1) + (sigma_rot2 * sigma_rot2);

    const double twist_var_v = pose_var_xy  / (dt * dt);
    const double twist_var_w = pose_var_yaw / (dt * dt);

    odom_msg.pose.covariance[0]  = pose_var_xy;
    odom_msg.pose.covariance[7]  = pose_var_xy;
    odom_msg.pose.covariance[14] = 1e-9;
    odom_msg.pose.covariance[21] = 1e-9;
    odom_msg.pose.covariance[28] = 1e-9;
    odom_msg.pose.covariance[35] = pose_var_yaw;

    odom_msg.twist.covariance[0]  = twist_var_v;
    odom_msg.twist.covariance[7]  = 1e-9;
    odom_msg.twist.covariance[14] = 1e-9;
    odom_msg.twist.covariance[21] = 1e-9;
    odom_msg.twist.covariance[28] = 1e-9;
    odom_msg.twist.covariance[35] = twist_var_w;

    ros_pub_->publish(odom_msg);

    // Store the true pose only to extract the next real motion increment.
    last_true_pose_ = current_true_pose;
  }
}