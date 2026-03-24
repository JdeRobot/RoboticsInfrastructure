#include "gz_noisy_odometry/NoisyOdometryPlugin.hpp"
#include <gz/sim/components/Pose.hh>
#include <gz/plugin/Register.hh>
#include <tf2/LinearMath/Quaternion.h>

GZ_ADD_PLUGIN(
    custom_plugins::NoisyOdometryPlugin,
    gz::sim::System,
    custom_plugins::NoisyOdometryPlugin::ISystemConfigure,
    custom_plugins::NoisyOdometryPlugin::ISystemPostUpdate)

GZ_ADD_PLUGIN_ALIAS(custom_plugins::NoisyOdometryPlugin, "custom_plugins::NoisyOdometryPlugin")

namespace custom_plugins
{
  NoisyOdometryPlugin::NoisyOdometryPlugin() : generator_(std::random_device{}())
  {
  }

  void NoisyOdometryPlugin::Configure(const gz::sim::Entity &_entity,
                                      const std::shared_ptr<const sdf::Element> &_sdf,
                                      gz::sim::EntityComponentManager &_ecm,
                                      gz::sim::EventManager &/*_eventMgr*/)
  {
    model_ = gz::sim::Model(_entity);

    if (!model_.Valid(_ecm))
    {
      return;
    }

    double linear_std_dev = _sdf->Get<double>("linear_noise_std_dev", 0.05).first;
    double angular_std_dev = _sdf->Get<double>("angular_noise_std_dev", 0.05).first;

    linear_noise_dist_ = std::normal_distribution<double>(0.0, linear_std_dev);
    angular_noise_dist_ = std::normal_distribution<double>(0.0, angular_std_dev);

    ros_topic_ = _sdf->Get<std::string>("ros_topic", "/noisy_odom").first;
    gz_cmd_vel_topic_ = _sdf->Get<std::string>("gz_cmd_vel_topic", "/cmd_vel").first;
    frame_id_ = _sdf->Get<std::string>("frame_id", "odom").first;
    child_frame_id_ = _sdf->Get<std::string>("child_frame_id", "base_link").first;

    gz_node_.Subscribe(gz_cmd_vel_topic_, &NoisyOdometryPlugin::OnCmdVel, this);

    if (!rclcpp::ok())
    {
      rclcpp::init(0, nullptr);
    }

    ros_node_ = rclcpp::Node::make_shared("noisy_odometry_node_" + model_.Name(_ecm));
    
    rclcpp::QoS qos(rclcpp::KeepLast(10));
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
    if (_info.paused)
    {
      return;
    }

    if (!initialized_)
    {
      auto poseComp = _ecm.Component<gz::sim::components::Pose>(model_.Entity());
      if (poseComp)
      {
        current_pose_ = poseComp->Data();
        initialized_ = true;
      }
      return;
    }

    double dt = std::chrono::duration<double>(_info.dt).count();
    
    if (dt <= 0.0)
    {
      return;
    }

    double v_cmd, w_cmd;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      v_cmd = current_v_;
      w_cmd = current_w_;
    }

    double v_noisy = v_cmd + linear_noise_dist_(generator_);
    double w_noisy = w_cmd + angular_noise_dist_(generator_);

    double yaw = current_pose_.Yaw();
    double dx = v_noisy * cos(yaw + (w_noisy * dt / 2.0)) * dt;
    double dy = v_noisy * sin(yaw + (w_noisy * dt / 2.0)) * dt;
    double dyaw = w_noisy * dt;

    current_pose_.Pos().X() += dx;
    current_pose_.Pos().Y() += dy;
    
    gz::math::Quaterniond new_rot;
    new_rot.SetFromEuler(0.0, 0.0, yaw + dyaw);
    current_pose_.Rot() = new_rot;

    nav_msgs::msg::Odometry odom_msg;
    odom_msg.header.stamp = ros_node_->now();
    odom_msg.header.frame_id = frame_id_;
    odom_msg.child_frame_id = child_frame_id_;

    odom_msg.pose.pose.position.x = current_pose_.Pos().X();
    odom_msg.pose.pose.position.y = current_pose_.Pos().Y();
    odom_msg.pose.pose.position.z = current_pose_.Pos().Z();

    tf2::Quaternion q;
    q.setRPY(0.0, 0.0, current_pose_.Yaw());
    odom_msg.pose.pose.orientation.x = q.x();
    odom_msg.pose.pose.orientation.y = q.y();
    odom_msg.pose.pose.orientation.z = q.z();
    odom_msg.pose.pose.orientation.w = q.w();

    odom_msg.twist.twist.linear.x = v_noisy;
    odom_msg.twist.twist.angular.z = w_noisy;

    ros_pub_->publish(odom_msg);
  }
}