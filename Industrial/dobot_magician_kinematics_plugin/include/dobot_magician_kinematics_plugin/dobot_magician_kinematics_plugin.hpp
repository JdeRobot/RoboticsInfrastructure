#pragma once

#include <moveit/kinematics_base/kinematics_base.h>

namespace dobot_magician_kinematics_plugin
{

// Analytic IK for the Dobot Magician arm (joint_1..joint_4). The group
// isn't a real kinematic chain, the parallelogram's two mimic joints sit
// between joint_3 and joint_4, so KDL/TRAC-IK can't be used here, see
// dobot_magician_gripper.srdf. This solves the closed form directly
// instead, same geometry as the pick_place solution's own IK.
class DobotMagicianKinematicsPlugin : public kinematics::KinematicsBase
{
public:
  DobotMagicianKinematicsPlugin() = default;

  bool initialize(const rclcpp::Node::SharedPtr& node, const moveit::core::RobotModel& robot_model,
                   const std::string& group_name, const std::string& base_frame,
                   const std::vector<std::string>& tip_frames, double search_discretization) override;

  bool getPositionIK(const geometry_msgs::msg::Pose& ik_pose, const std::vector<double>& ik_seed_state,
                      std::vector<double>& solution, moveit_msgs::msg::MoveItErrorCodes& error_code,
                      const kinematics::KinematicsQueryOptions& options = kinematics::KinematicsQueryOptions())
      const override;

  bool searchPositionIK(
      const geometry_msgs::msg::Pose& ik_pose, const std::vector<double>& ik_seed_state, double timeout,
      std::vector<double>& solution, moveit_msgs::msg::MoveItErrorCodes& error_code,
      const kinematics::KinematicsQueryOptions& options = kinematics::KinematicsQueryOptions()) const override;

  bool searchPositionIK(
      const geometry_msgs::msg::Pose& ik_pose, const std::vector<double>& ik_seed_state, double timeout,
      const std::vector<double>& consistency_limits, std::vector<double>& solution,
      moveit_msgs::msg::MoveItErrorCodes& error_code,
      const kinematics::KinematicsQueryOptions& options = kinematics::KinematicsQueryOptions()) const override;

  bool searchPositionIK(
      const geometry_msgs::msg::Pose& ik_pose, const std::vector<double>& ik_seed_state, double timeout,
      std::vector<double>& solution, const IKCallbackFn& solution_callback,
      moveit_msgs::msg::MoveItErrorCodes& error_code,
      const kinematics::KinematicsQueryOptions& options = kinematics::KinematicsQueryOptions()) const override;

  bool searchPositionIK(
      const geometry_msgs::msg::Pose& ik_pose, const std::vector<double>& ik_seed_state, double timeout,
      const std::vector<double>& consistency_limits, std::vector<double>& solution,
      const IKCallbackFn& solution_callback,
      moveit_msgs::msg::MoveItErrorCodes& error_code,
      const kinematics::KinematicsQueryOptions& options = kinematics::KinematicsQueryOptions()) const override;

  bool getPositionFK(const std::vector<std::string>& link_names, const std::vector<double>& joint_angles,
                      std::vector<geometry_msgs::msg::Pose>& poses) const override;

  bool supportsGroup(const moveit::core::JointModelGroup* jmg, std::string* error_text_out = nullptr) const override;

  const std::vector<std::string>& getJointNames() const override;
  const std::vector<std::string>& getLinkNames() const override;

private:
  // Solves for (joint_2, joint_3) reaching the given (radius, height) in
  // the vertical plane the arm is already facing, joint_1 handles the
  // azimuth separately. Tries elbow-up and elbow-down, returns the first
  // one inside both joints' limits. radius already has the wrist offset
  // (L4) removed.
  bool solveShoulderElbow(double radius, double height, double& joint2, double& joint3) const;

  bool solveIK(const geometry_msgs::msg::Pose& ik_pose, std::vector<double>& solution,
               moveit_msgs::msg::MoveItErrorCodes& error_code) const;

  std::vector<std::string> joint_names_;
  std::vector<std::string> link_names_;

  // Rear arm, forearm, wrist offset, meters, matches
  // dobot_magician_macro.xacro
  static constexpr double kRearArmLength = 0.135;
  static constexpr double kForearmLength = 0.147;
  static constexpr double kWristOffset = 0.06;

  static constexpr double kJoint1Lower = -125.0 * M_PI / 180.0;
  static constexpr double kJoint1Upper = 125.0 * M_PI / 180.0;
  static constexpr double kJoint2Lower = -5.0 * M_PI / 180.0;
  static constexpr double kJoint2Upper = 90.0 * M_PI / 180.0;
  static constexpr double kJoint3Lower = -15.0 * M_PI / 180.0;
  static constexpr double kJoint3Upper = 70.0 * M_PI / 180.0;
  static constexpr double kJoint4Lower = -150.0 * M_PI / 180.0;
  static constexpr double kJoint4Upper = 150.0 * M_PI / 180.0;
};

}  // namespace dobot_magician_kinematics_plugin
