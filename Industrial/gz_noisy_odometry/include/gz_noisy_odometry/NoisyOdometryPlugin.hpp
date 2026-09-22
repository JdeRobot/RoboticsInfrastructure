#ifndef NOISY_ODOMETRY_PLUGIN_HPP_
#define NOISY_ODOMETRY_PLUGIN_HPP_

#include <gz/math/Rand.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/System.hh>

#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>

#include <memory>
#include <string>

namespace custom_plugins {
class NoisyOdometryPlugin : public gz::sim::System,
                            public gz::sim::ISystemConfigure,
                            public gz::sim::ISystemPostUpdate {
public:
  NoisyOdometryPlugin();
  ~NoisyOdometryPlugin() override = default;

  void Configure(const gz::sim::Entity &_entity,
                 const std::shared_ptr<const sdf::Element> &_sdf,
                 gz::sim::EntityComponentManager &_ecm,
                 gz::sim::EventManager &_eventMgr) override;

  void PostUpdate(const gz::sim::UpdateInfo &_info,
                  const gz::sim::EntityComponentManager &_ecm) override;

private:
  double NormalizeAngle(double _angle) const;

  gz::sim::Model model_;

  std::shared_ptr<rclcpp::Node> ros_node_;
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr ros_pub_;

  std::string ros_topic_;
  std::string frame_id_;
  std::string child_frame_id_;

  // Odometry source: reconstruct from wheel encoders ("wheels", default) or
  // from the model pose delta ("pose"). Pose mode works for any drivetrain
  // (diff, ackermann, mecanum/omni) since it does not assume wheel kinematics.
  bool use_pose_source_{false};
  // Track lateral (y) motion — required for omnidirectional/mecanum robots.
  bool holonomic_{false};

  // Wheel joint entities resolved once in Configure (wheels source only).
  gz::sim::Entity left_joint_entity_{gz::sim::kNullEntity};
  gz::sim::Entity right_joint_entity_{gz::sim::kNullEntity};

  // Differential drive kinematics — must match the DiffDrive plugin values.
  double wheel_radius_{0.033};
  double wheel_separation_{0.287};

  // Last joint positions used to compute per-tick angle deltas.
  double last_left_pos_{0.0};
  double last_right_pos_{0.0};

  // Last model pose (world frame) used in pose-source mode.
  double last_pose_x_{0.0};
  double last_pose_y_{0.0};
  double last_pose_yaw_{0.0};

  std::chrono::steady_clock::duration last_update_time_{0};

  bool initialized_{false};

  // Accumulated noisy odometry estimate.
  double noisy_x_{0.0};
  double noisy_y_{0.0};
  double noisy_yaw_{0.0};

  // Standard odometry motion-model coefficients (Probabilistic Robotics, Ch.
  // 5).
  double alpha1_{0.0}; // rotation noise from rotation
  double alpha2_{0.0}; // rotation noise from translation
  double alpha3_{0.0}; // translation noise from translation
  double alpha4_{0.0}; // translation noise from rotation
};
} // namespace custom_plugins

#endif
