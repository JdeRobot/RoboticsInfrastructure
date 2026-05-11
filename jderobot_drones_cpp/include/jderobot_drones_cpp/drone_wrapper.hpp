#ifndef DRONE_WRAPPER_HPP
#define DRONE_WRAPPER_HPP

#include <as2_core/node.hpp>
#include <as2_msgs/msg/platform_info.hpp>
#include <as2_msgs/srv/set_platform_state_machine_event.hpp>
#include <as2_motion_reference_handlers/position_motion.hpp>
#include <as2_motion_reference_handlers/speed_motion.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <rclcpp/rclcpp.hpp>
#include <vector>

class DroneWrapper : public as2::Node {
public:
  DroneWrapper(const std::string &drone_id = "drone0");

  void setCmdPos(float x, float y, float z, float az);
  void setCmdVel(float vx, float vy, float vz, float az);
  void takeoff(float height);
  void land();

  std::vector<double> getPosition() { return {position_.x, position_.y, position_.z}; }
  std::vector<double> getOrientation() { return {orientation_.x, orientation_.y, orientation_.z}; }
  float getYawRate() const { return yaw_rate_; }
  int getLandedState() const { return static_cast<int>(state_); }

private:
  void yawRateCb(const geometry_msgs::msg::TwistStamped::SharedPtr msg);
  void infoCb(const as2_msgs::msg::PlatformInfo::SharedPtr msg);
  void targetCb(const geometry_msgs::msg::PoseStamped::SharedPtr msg);
  void callStateEvent(int8_t event);

  float yaw_rate_ = 0.0f;
  int8_t state_ = 0;
  geometry_msgs::msg::Vector3 position_;
  geometry_msgs::msg::Vector3 orientation_;
  geometry_msgs::msg::Pose target_pose_;

  std::shared_ptr<as2::motionReferenceHandlers::PositionMotion> pos_handler_;
  std::shared_ptr<as2::motionReferenceHandlers::SpeedMotion> speed_handler_;
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr yaw_sub_;
  rclcpp::Subscription<as2_msgs::msg::PlatformInfo>::SharedPtr info_sub_;
  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr target_sub_;
  rclcpp::Client<as2_msgs::srv::SetPlatformStateMachineEvent>::SharedPtr state_client_;
};

#endif