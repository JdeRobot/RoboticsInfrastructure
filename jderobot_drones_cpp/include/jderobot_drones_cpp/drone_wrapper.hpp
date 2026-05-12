#ifndef DRONE_WRAPPER_HPP
#define DRONE_WRAPPER_HPP

#include <as2_core/node.hpp>
#include <as2_msgs/msg/platform_info.hpp>
#include <as2_msgs/srv/set_platform_state_machine_event.hpp>
#include <as2_motion_reference_handlers/position_motion.hpp>
#include <as2_motion_reference_handlers/speed_motion.hpp>
#include <as2_motion_reference_handlers/speed_in_a_plane_motion.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <std_srvs/srv/set_bool.hpp>
#include <rclcpp/rclcpp.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/LinearMath/Matrix3x3.h>
#include <vector>

class DroneWrapper : public as2::Node {
public:
  DroneWrapper(const std::string &drone_id = "drone0");

  // Motion commands
  void setCmdPos(float x, float y, float z, float az);
  void setCmdVel(float vx, float vy, float vz, float az);
  void setCmdMix(float vx, float vy, float z, float az);

  // High-level blocking commands (mirror Python takeoff/land behaviour)
  void takeoff(float height);
  void land();

  // Getters
  std::vector<double> getPosition()    { return {position_.x, position_.y, position_.z}; }
  std::vector<double> getOrientation() { return {orientation_.x, orientation_.y, orientation_.z}; }
  std::vector<double> getVelocity()    { return {speed_.x, speed_.y, speed_.z}; }
  float getYawRate()    const { return yaw_rate_; }
  int   getLandedState() const { return static_cast<int>(state_); }

private:
  // Topic callbacks
  void yawRateCb(const geometry_msgs::msg::TwistStamped::SharedPtr msg);
  void infoCb(const as2_msgs::msg::PlatformInfo::SharedPtr msg);
  void targetCb(const geometry_msgs::msg::PoseStamped::SharedPtr msg);
  void poseCb(const geometry_msgs::msg::PoseStamped::SharedPtr msg);

  // Blocking service helpers — wait until the service replies before returning
  void callStateEventSync(int8_t event);
  void callSetBoolSync(rclcpp::Client<std_srvs::srv::SetBool>::SharedPtr client, bool value);

  // Internal state
  float yaw_rate_ = 0.0f;
  int8_t state_   = 0;
  geometry_msgs::msg::Vector3 position_;
  geometry_msgs::msg::Vector3 orientation_;
  geometry_msgs::msg::Vector3 speed_;
  geometry_msgs::msg::Pose target_pose_;
  std::string base_link_frame_;

  // Motion-reference handlers
  std::shared_ptr<as2::motionReferenceHandlers::PositionMotion>      pos_handler_;
  std::shared_ptr<as2::motionReferenceHandlers::SpeedMotion>         speed_handler_;
  std::shared_ptr<as2::motionReferenceHandlers::SpeedInAPlaneMotion> speed_in_plane_handler_;

  // Subscriptions
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr yaw_sub_;
  rclcpp::Subscription<as2_msgs::msg::PlatformInfo>::SharedPtr      info_sub_;
  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr  target_sub_;
  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr  pose_sub_;

  // Service clients — kept in a dedicated MutuallyExclusive callback group so
  // that spin_until_future_complete() can drain their futures even while the
  // MultiThreadedExecutor in HAL is already spinning the node's other callbacks.
  rclcpp::CallbackGroup::SharedPtr service_cb_group_;
  rclcpp::Client<as2_msgs::srv::SetPlatformStateMachineEvent>::SharedPtr state_client_;
  rclcpp::Client<std_srvs::srv::SetBool>::SharedPtr arm_client_;
  rclcpp::Client<std_srvs::srv::SetBool>::SharedPtr offboard_client_;
};

#endif // DRONE_WRAPPER_HPP