#ifndef ZIMMER_GRIPPER__GRIPPER_SERVER_HPP_
#define ZIMMER_GRIPPER__GRIPPER_SERVER_HPP_

#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

#include "ur_msgs/srv/set_io.hpp"

#include "zimmer_gripper/action/gripper.hpp"

class ZimmerGripperServer : public rclcpp::Node
{
public:
  using Gripper = zimmer_gripper::action::Gripper;
  using GoalHandleGripper = rclcpp_action::ServerGoalHandle<Gripper>;

  ZimmerGripperServer();

private:

  // Action Server
  rclcpp_action::Server<Gripper>::SharedPtr action_server_;

  // Cliente del servicio SetIO del driver UR
  rclcpp::Client<ur_msgs::srv::SetIO>::SharedPtr io_client_;

  // ===== Callbacks del Action Server =====

  rclcpp_action::GoalResponse handle_goal(
      const rclcpp_action::GoalUUID & uuid,
      std::shared_ptr<const Gripper::Goal> goal);

  rclcpp_action::CancelResponse handle_cancel(
      const std::shared_ptr<GoalHandleGripper> goal_handle);

  void handle_accepted(
      const std::shared_ptr<GoalHandleGripper> goal_handle);

  void execute(
      const std::shared_ptr<GoalHandleGripper> goal_handle);

  // ===== Funciones auxiliares =====

  bool setToolOutput(uint8_t pin, bool state);

  bool openGripper();

  bool closeGripper();
};

#endif