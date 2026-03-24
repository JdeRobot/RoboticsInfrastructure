#include "gz_noisy_odometry/NoisyOdometryPlugin.hpp"
#include <gz/sim/components/Pose.hpp>
#include <gz/plugin/Register.hpp>
#include <tf2/LinearMath/Quaternion.h>

GZ_ADD_PLUGIN(
    custom_plugins::NoisyOdometryPlugin,
    gz::sim::System,
    custom_plugins::NoisyOdometryPlugin::ISystemConfigure,
    custom_plugins::NoisyOdometryPlugin::ISystemPostUpdate)

GZ_ADD_PLUGIN_ALIAS(custom_plugins::NoisyOdometryPlugin, "custom_plugins::NoisyOdometryPlugin")

namespace custom_plugins
{
  NoisyOdometryPlugin::NoisyOdometryPlugin() {}

  void NoisyOdometryPlugin::Configure(const gz::sim::Entity &_entity,
                                      const std::shared_ptr<const sdf::Element> &_sdf,
                                      gz::sim::EntityComponentManager &_ecm,
                                      gz::sim::EventManager &)
  {
    model_ = gz::sim::Model(_entity);
    if (!model_.Valid(_ecm)) return;

    // Parámetros del SDF
    gaussian_noise_coeff_ = _sdf->Get<double>("gaussian_noise", 0.05).first;
    ros_topic_ = _sdf->Get<std::string>("ros_topic", "/turtlebot3/odom_noisy").first;
    gz_cmd_vel_topic_ = _sdf->Get<std::string>("gz_cmd_vel_topic", "/turtlebot3/cmd_vel").first;
    frame_id_ = _sdf->Get<std::string>("frame_id", "odom").first;
    child_frame_id_ = _sdf->Get<std::string>("child_frame_id", "base_footprint").first;

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

    if (!initialized_)
    {
      auto poseComp = _ecm.Component<gz::sim::components::Pose>(model_.Entity());
      if (poseComp) {
        noisy_pose_internal_ = poseComp->Data();
        last_update_time_ = _info.simTime;
        initialized_ = true;
      }
      return;
    }

    double dt = std::chrono::duration<double>(_info.simTime - last_update_time_).count();
    if (dt <= 0.0) return;
    last_update_time_ = _info.simTime;

    double v_cmd, w_cmd;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      v_cmd = current_v_;
      w_cmd = current_w_;
    }

    // MATEMÁTICA HÍBRIDA: Integración Estocástica Proporcional
    // El ruido es proporcional a la velocidad y escalado por sqrt(dt) para un Random Walk correcto
    double linear_noise = gaussian_noise_coeff_ * gz::math::Rand::DblNormal(0, 1) * std::sqrt(dt) * std::abs(v_cmd);
    double angular_noise = gaussian_noise_coeff_ * gz::math::Rand::DblNormal(0, 1) * std::sqrt(dt) * std::abs(w_cmd);

    double v_noisy = v_cmd + (linear_noise / dt);
    double w_noisy = w_cmd + (angular_noise / dt);

    // Actualización de orientación (Yaw)
    double yaw_prev = noisy_pose_internal_.Rot().Yaw();
    double yaw_new = yaw_prev + (w_noisy * dt);
    
    // Actualización de posición (Cinemática Diferencial)
    double distance = v_noisy * dt;
    noisy_pose_internal_.Pos().X() += distance * std::cos(yaw_prev + (w_noisy * dt / 2.0));
    noisy_pose_internal_.Pos().Y() += distance * std::sin(yaw_prev + (w_noisy * dt / 2.0));
    
    gz::math::Quaterniond q_new;
    q_new.SetFromEuler(0, 0, yaw_new);
    noisy_pose_internal_.Rot() = q_new;

    // Publicación en ROS 2
    nav_msgs::msg::Odometry odom_msg;
    odom_msg.header.stamp = ros_node_->now();
    odom_msg.header.frame_id = frame_id_;
    odom_msg.child_frame_id = child_frame_id_;

    odom_msg.pose.pose.position.x = noisy_pose_internal_.Pos().X();
    odom_msg.pose.pose.position.y = noisy_pose_internal_.Pos().Y();
    
    tf2::Quaternion q;
    q.setRPY(0, 0, yaw_new);
    odom_msg.pose.pose.orientation.x = q.x();
    odom_msg.pose.pose.orientation.y = q.y();
    odom_msg.pose.pose.orientation.z = q.z();
    odom_msg.pose.pose.orientation.w = q.w();

    odom_msg.twist.twist.linear.x = v_noisy;
    odom_msg.twist.twist.angular.z = w_noisy;

    ros_pub_->publish(odom_msg);
  }
}