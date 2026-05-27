#include "gz_noisy_odometry/NoisyOdometryPlugin.hpp"
#include <gz/sim/components/JointPosition.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/plugin/Register.hh>

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
    while (_angle > M_PI)  _angle -= 2.0 * M_PI;
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

    // Kinematics — must match the DiffDrive plugin values in the same SDF.
    wheel_radius_     = _sdf->Get<double>("wheel_radius",     0.033).first;
    wheel_separation_ = _sdf->Get<double>("wheel_separation", 0.287).first;

    const std::string left_joint_name  = _sdf->Get<std::string>("left_joint",  "wheel_left_joint").first;
    const std::string right_joint_name = _sdf->Get<std::string>("right_joint", "wheel_right_joint").first;

    ros_topic_      = _sdf->Get<std::string>("ros_topic",      "/turtlebot3/odom_noisy").first;
    frame_id_       = _sdf->Get<std::string>("frame_id",       "odom").first;
    child_frame_id_ = _sdf->Get<std::string>("child_frame_id", "base_footprint").first;

    // A single gaussian_noise value maps to all alphas as a convenience fallback.
    const double default_noise = _sdf->Get<double>("gaussian_noise", 0.05).first;
    alpha1_ = _sdf->Get<double>("alpha1", default_noise).first;
    alpha2_ = _sdf->Get<double>("alpha2", default_noise).first;
    alpha3_ = _sdf->Get<double>("alpha3", default_noise).first;
    alpha4_ = _sdf->Get<double>("alpha4", default_noise).first;

    // Resolve wheel joints and request JointPosition so Gazebo tracks them from step 0.
    left_joint_entity_  = model_.JointByName(_ecm, left_joint_name);
    right_joint_entity_ = model_.JointByName(_ecm, right_joint_name);

    if (left_joint_entity_  == gz::sim::kNullEntity ||
        right_joint_entity_ == gz::sim::kNullEntity)
    {
      gzerr << "[NoisyOdometryPlugin] Wheel joints not found: '"
            << left_joint_name << "', '" << right_joint_name << "'\n";
      return;
    }

    _ecm.CreateComponent(left_joint_entity_,  gz::sim::components::JointPosition());
    _ecm.CreateComponent(right_joint_entity_, gz::sim::components::JointPosition());

    if (!rclcpp::ok()) rclcpp::init(0, nullptr);
    ros_node_ = rclcpp::Node::make_shared("noisy_odom_node_" + model_.Name(_ecm));

    rclcpp::QoS qos(10);
    qos.transient_local();
    ros_pub_ = ros_node_->create_publisher<nav_msgs::msg::Odometry>(ros_topic_, qos);
  }

  void NoisyOdometryPlugin::PostUpdate(const gz::sim::UpdateInfo &_info,
                                       const gz::sim::EntityComponentManager &_ecm)
  {
    if (_info.paused) return;

    auto *leftComp  = _ecm.Component<gz::sim::components::JointPosition>(left_joint_entity_);
    auto *rightComp = _ecm.Component<gz::sim::components::JointPosition>(right_joint_entity_);

    if (!leftComp || !rightComp ||
        leftComp->Data().empty() || rightComp->Data().empty()) return;

    const double left_pos  = leftComp->Data()[0];
    const double right_pos = rightComp->Data()[0];

    if (!initialized_)
    {
      // Seed the estimate with the robot's spawn pose so that odom_noisy starts
      // at the same position as the perfect-odometry topic.  After this point
      // the estimate evolves purely from encoder increments — Pose is not read again.
      auto *poseComp = _ecm.Component<gz::sim::components::Pose>(model_.Entity());
      if (poseComp)
      {
        noisy_x_   = poseComp->Data().Pos().X();
        noisy_y_   = poseComp->Data().Pos().Y();
        noisy_yaw_ = poseComp->Data().Rot().Yaw();
      }

      last_left_pos_    = left_pos;
      last_right_pos_   = right_pos;
      last_update_time_ = _info.simTime;
      initialized_      = true;
      return;
    }

    const double dt =
      std::chrono::duration<double>(_info.simTime - last_update_time_).count();

    if (dt <= 0.0) return;
    last_update_time_ = _info.simTime;

    // Per-tick wheel angle increments — the encoder analog.
    // When the robot is blocked against a wall the wheel joints still rotate
    // (the motor keeps spinning), so drift accumulates naturally without any
    // special-case logic, exactly as real encoders would behave.
    const double d_left  = left_pos  - last_left_pos_;
    const double d_right = right_pos - last_right_pos_;

    last_left_pos_  = left_pos;
    last_right_pos_ = right_pos;

    // Differential drive kinematics: arc lengths into linear and angular motion.
    const double ds     = wheel_radius_ * (d_right + d_left)  / 2.0;
    const double dtheta = wheel_radius_ * (d_right - d_left) / wheel_separation_;

    // Odometry motion-model noise (Probabilistic Robotics, Ch. 5).
    // Translation error grows with distance and heading change; rotation error
    // grows with heading change and distance — both accumulate over time.
    const double sigma_trans = alpha3_ * std::abs(ds)     + alpha4_ * std::abs(dtheta);
    const double sigma_rot   = alpha1_ * std::abs(dtheta) + alpha2_ * std::abs(ds);

    const double ds_noisy     = ds     + gz::math::Rand::DblNormal(0.0, sigma_trans);
    const double dtheta_noisy = dtheta + gz::math::Rand::DblNormal(0.0, sigma_rot);

    // Integrate using the midpoint heading to reduce discretisation error.
    const double heading_mid = noisy_yaw_ + dtheta_noisy / 2.0;
    noisy_x_   += ds_noisy * std::cos(heading_mid);
    noisy_y_   += ds_noisy * std::sin(heading_mid);
    noisy_yaw_  = NormalizeAngle(noisy_yaw_ + dtheta_noisy);

    nav_msgs::msg::Odometry odom_msg;
    odom_msg.header.stamp    = ros_node_->now();
    odom_msg.header.frame_id = frame_id_;
    odom_msg.child_frame_id  = child_frame_id_;

    odom_msg.pose.pose.position.x = noisy_x_;
    odom_msg.pose.pose.position.y = noisy_y_;
    odom_msg.pose.pose.position.z = 0.0;

    // Planar robot: roll = pitch = 0, only yaw.
    odom_msg.pose.pose.orientation.x = 0.0;
    odom_msg.pose.pose.orientation.y = 0.0;
    odom_msg.pose.pose.orientation.z = std::sin(noisy_yaw_ / 2.0);
    odom_msg.pose.pose.orientation.w = std::cos(noisy_yaw_ / 2.0);

    // Twist consistent with the noisy increment just integrated.
    odom_msg.twist.twist.linear.x  = ds_noisy     / dt;
    odom_msg.twist.twist.linear.y  = 0.0;
    odom_msg.twist.twist.linear.z  = 0.0;
    odom_msg.twist.twist.angular.x = 0.0;
    odom_msg.twist.twist.angular.y = 0.0;
    odom_msg.twist.twist.angular.z = dtheta_noisy / dt;

    // Covariance entries consistent with the motion-model sigmas.
    const double pose_var_xy  = sigma_trans * sigma_trans;
    const double pose_var_yaw = sigma_rot   * sigma_rot;

    odom_msg.pose.covariance[0]  = pose_var_xy;
    odom_msg.pose.covariance[7]  = pose_var_xy;
    odom_msg.pose.covariance[14] = 1e-9;
    odom_msg.pose.covariance[21] = 1e-9;
    odom_msg.pose.covariance[28] = 1e-9;
    odom_msg.pose.covariance[35] = pose_var_yaw;

    odom_msg.twist.covariance[0]  = pose_var_xy  / (dt * dt);
    odom_msg.twist.covariance[7]  = 1e-9;
    odom_msg.twist.covariance[14] = 1e-9;
    odom_msg.twist.covariance[21] = 1e-9;
    odom_msg.twist.covariance[28] = 1e-9;
    odom_msg.twist.covariance[35] = pose_var_yaw / (dt * dt);

    ros_pub_->publish(odom_msg);
  }
}
