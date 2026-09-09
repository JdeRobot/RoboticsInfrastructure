#include "dobot_magician_kinematics_plugin/dobot_magician_kinematics_plugin.hpp"

#include <cmath>

#include <moveit/robot_model/robot_model.h>
#include <pluginlib/class_list_macros.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/utils.h>

namespace dobot_magician_kinematics_plugin
{

bool DobotMagicianKinematicsPlugin::initialize(const rclcpp::Node::SharedPtr& node,
                                                const moveit::core::RobotModel& robot_model,
                                                const std::string& group_name, const std::string& base_frame,
                                                const std::vector<std::string>& tip_frames,
                                                double search_discretization)
{
  storeValues(robot_model, group_name, base_frame, tip_frames, search_discretization);
  (void)node;

  joint_names_ = { "joint_1", "joint_2", "joint_3", "joint_4" };
  link_names_ = { "link_1", "link_2", "link_3", "link_gripper_core" };

  const moveit::core::JointModelGroup* jmg = robot_model.getJointModelGroup(group_name);

  RCLCPP_INFO(rclcpp::get_logger("dobot_magician_kinematics_plugin"),
              "initialize() group=%s base_frame=%s jmg_found=%d", group_name.c_str(), base_frame.c_str(),
              jmg != nullptr);

  if (!jmg)
  {
    return false;
  }

  return true;
}

bool DobotMagicianKinematicsPlugin::supportsGroup(const moveit::core::JointModelGroup* /*jmg*/,
                                                   std::string* /*error_text_out*/) const
{
  // The group is a joint list, not a chain, on purpose, see the header
  // comment. That's fine here, this solver doesn't walk the URDF tree.
  return true;
}

const std::vector<std::string>& DobotMagicianKinematicsPlugin::getJointNames() const
{
  return joint_names_;
}

const std::vector<std::string>& DobotMagicianKinematicsPlugin::getLinkNames() const
{
  return link_names_;
}

bool DobotMagicianKinematicsPlugin::solveShoulderElbow(double radius, double height, double& joint2,
                                                        double& joint3) const
{
  const double dist_sq = radius * radius + height * height;

  double cos_elbow = (dist_sq - kRearArmLength * kRearArmLength - kForearmLength * kForearmLength) /
                      (2.0 * kRearArmLength * kForearmLength);

  if (cos_elbow > 1.0 || cos_elbow < -1.0)
  {
    // Target outside the reachable annulus (too far or too close)
    return false;
  }

  for (double sign : { 1.0, -1.0 })
  {
    const double elbow_angle = sign * std::acos(cos_elbow);

    const double shoulder_from_horizontal =
        std::atan2(height, radius) -
        std::atan2(kForearmLength * std::sin(elbow_angle), kRearArmLength + kForearmLength * std::cos(elbow_angle));

    const double forearm_absolute = shoulder_from_horizontal + elbow_angle;

    const double j2 = M_PI_2 - shoulder_from_horizontal;
    const double j3 = -forearm_absolute - j2;

    if (j2 >= kJoint2Lower && j2 <= kJoint2Upper && j3 >= kJoint3Lower && j3 <= kJoint3Upper)
    {
      joint2 = j2;
      joint3 = j3;
      return true;
    }
  }

  return false;
}

bool DobotMagicianKinematicsPlugin::solveIK(const geometry_msgs::msg::Pose& ik_pose, std::vector<double>& solution,
                                             moveit_msgs::msg::MoveItErrorCodes& error_code) const
{
  const double x = ik_pose.position.x;
  const double y = ik_pose.position.y;
  const double z = ik_pose.position.z;

  RCLCPP_INFO(rclcpp::get_logger("dobot_magician_kinematics_plugin"), "solveIK() target x=%.4f y=%.4f z=%.4f", x, y,
              z);

  const double joint1 = std::atan2(y, x);

  if (joint1 < kJoint1Lower || joint1 > kJoint1Upper)
  {
    RCLCPP_INFO(rclcpp::get_logger("dobot_magician_kinematics_plugin"), "solveIK() joint1=%.4f out of range", joint1);
    error_code.val = moveit_msgs::msg::MoveItErrorCodes::NO_IK_SOLUTION;
    return false;
  }

  const double radius = std::hypot(x, y) - kWristOffset;

  double joint2 = 0.0;
  double joint3 = 0.0;

  if (!solveShoulderElbow(radius, z, joint2, joint3))
  {
    RCLCPP_INFO(rclcpp::get_logger("dobot_magician_kinematics_plugin"),
                "solveIK() no shoulder/elbow solution for radius=%.4f height=%.4f", radius, z);
    error_code.val = moveit_msgs::msg::MoveItErrorCodes::NO_IK_SOLUTION;
    return false;
  }

  // The parallelogram cancels joint_2/joint_3 out of the wrist's own
  // orientation, so the gripper can only yaw, tf2::getYaw on whatever
  // orientation was asked for is the only usable part of it
  const double target_yaw = tf2::getYaw(ik_pose.orientation);
  double joint4 = target_yaw - joint1;

  while (joint4 > M_PI)
    joint4 -= 2.0 * M_PI;
  while (joint4 < -M_PI)
    joint4 += 2.0 * M_PI;

  if (joint4 < kJoint4Lower || joint4 > kJoint4Upper)
  {
    error_code.val = moveit_msgs::msg::MoveItErrorCodes::NO_IK_SOLUTION;
    return false;
  }

  solution = { joint1, joint2, joint3, joint4 };
  error_code.val = moveit_msgs::msg::MoveItErrorCodes::SUCCESS;

  RCLCPP_INFO(rclcpp::get_logger("dobot_magician_kinematics_plugin"),
              "solveIK() SUCCESS joint1=%.4f joint2=%.4f joint3=%.4f joint4=%.4f", joint1, joint2, joint3, joint4);

  return true;
}

bool DobotMagicianKinematicsPlugin::getPositionIK(const geometry_msgs::msg::Pose& ik_pose,
                                                   const std::vector<double>& /*ik_seed_state*/,
                                                   std::vector<double>& solution,
                                                   moveit_msgs::msg::MoveItErrorCodes& error_code,
                                                   const kinematics::KinematicsQueryOptions& /*options*/) const
{
  return solveIK(ik_pose, solution, error_code);
}

bool DobotMagicianKinematicsPlugin::searchPositionIK(const geometry_msgs::msg::Pose& ik_pose,
                                                      const std::vector<double>& ik_seed_state, double /*timeout*/,
                                                      std::vector<double>& solution,
                                                      moveit_msgs::msg::MoveItErrorCodes& error_code,
                                                      const kinematics::KinematicsQueryOptions& options) const
{
  return getPositionIK(ik_pose, ik_seed_state, solution, error_code, options);
}

bool DobotMagicianKinematicsPlugin::searchPositionIK(const geometry_msgs::msg::Pose& ik_pose,
                                                      const std::vector<double>& ik_seed_state, double /*timeout*/,
                                                      const std::vector<double>& /*consistency_limits*/,
                                                      std::vector<double>& solution,
                                                      moveit_msgs::msg::MoveItErrorCodes& error_code,
                                                      const kinematics::KinematicsQueryOptions& options) const
{
  return getPositionIK(ik_pose, ik_seed_state, solution, error_code, options);
}

bool DobotMagicianKinematicsPlugin::searchPositionIK(const geometry_msgs::msg::Pose& ik_pose,
                                                      const std::vector<double>& ik_seed_state, double /*timeout*/,
                                                      std::vector<double>& solution,
                                                      const IKCallbackFn& solution_callback,
                                                      moveit_msgs::msg::MoveItErrorCodes& error_code,
                                                      const kinematics::KinematicsQueryOptions& options) const
{
  if (!getPositionIK(ik_pose, ik_seed_state, solution, error_code, options))
  {
    return false;
  }

  if (solution_callback)
  {
    solution_callback(ik_pose, solution, error_code);
  }

  return error_code.val == moveit_msgs::msg::MoveItErrorCodes::SUCCESS;
}

bool DobotMagicianKinematicsPlugin::searchPositionIK(const geometry_msgs::msg::Pose& ik_pose,
                                                      const std::vector<double>& ik_seed_state, double /*timeout*/,
                                                      const std::vector<double>& /*consistency_limits*/,
                                                      std::vector<double>& solution,
                                                      const IKCallbackFn& solution_callback,
                                                      moveit_msgs::msg::MoveItErrorCodes& error_code,
                                                      const kinematics::KinematicsQueryOptions& options) const
{
  if (!getPositionIK(ik_pose, ik_seed_state, solution, error_code, options))
  {
    return false;
  }

  if (solution_callback)
  {
    solution_callback(ik_pose, solution, error_code);
  }

  return error_code.val == moveit_msgs::msg::MoveItErrorCodes::SUCCESS;
}

bool DobotMagicianKinematicsPlugin::getPositionFK(const std::vector<std::string>& link_names,
                                                   const std::vector<double>& joint_angles,
                                                   std::vector<geometry_msgs::msg::Pose>& poses) const
{
  if (joint_angles.size() != 4)
  {
    return false;
  }

  const double joint1 = joint_angles[0];
  const double joint2 = joint_angles[1];
  const double joint3 = joint_angles[2];
  const double joint4 = joint_angles[3];

  const double radius =
      kRearArmLength * std::sin(joint2) + kForearmLength * std::cos(joint2 + joint3) + kWristOffset;
  const double height = kRearArmLength * std::cos(joint2) - kForearmLength * std::sin(joint2 + joint3);

  geometry_msgs::msg::Pose tip_pose;
  tip_pose.position.x = radius * std::cos(joint1);
  tip_pose.position.y = radius * std::sin(joint1);
  tip_pose.position.z = height;

  tf2::Quaternion q;
  q.setRPY(0.0, 0.0, joint1 + joint4);
  tip_pose.orientation.x = q.x();
  tip_pose.orientation.y = q.y();
  tip_pose.orientation.z = q.z();
  tip_pose.orientation.w = q.w();

  poses.clear();

  for (const auto& link_name : link_names)
  {
    if (link_name == link_names_.back())
    {
      poses.push_back(tip_pose);
    }
    else
    {
      // Only the tip is solved analytically here, intermediate links
      // aren't needed by anything that calls FK on this plugin
      return false;
    }
  }

  return true;
}

}  // namespace dobot_magician_kinematics_plugin

PLUGINLIB_EXPORT_CLASS(dobot_magician_kinematics_plugin::DobotMagicianKinematicsPlugin, kinematics::KinematicsBase)
