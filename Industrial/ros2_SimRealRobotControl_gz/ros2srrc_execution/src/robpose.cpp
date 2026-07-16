/*
# ===================================== COPYRIGHT ===================================== #
#                                                                                       #
#  IFRA (Intelligent Flexible Robotics and Assembly) Group, CRANFIELD UNIVERSITY        #
#  Created on behalf of the IFRA Group at Cranfield University, United Kingdom          #
#  E-mail: IFRA@cranfield.ac.uk                                                         #
#                                                                                       #
#  Licensed under the Apache-2.0 License.                                               #
#  You may not use this file except in compliance with the License.                     #
#  You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0  #
#                                                                                       #
#  Unless required by applicable law or agreed to in writing, software distributed      #
#  under the License is distributed on an "as-is" basis, without warranties or          #
#  conditions of any kind, either express or implied. See the License for the specific  #
#  language governing permissions and limitations under the License.                    #
#                                                                                       #
#  IFRA Group - Cranfield University                                                    #
#  AUTHORS: Mikel Bueno Viso - Mikel.Bueno-Viso@cranfield.ac.uk                         #
#           Dr. Seemal Asif  - s.asif@cranfield.ac.uk                                   #
#           Prof. Phil Webb  - p.f.webb@cranfield.ac.uk                                 #
#                                                                                       #
#  Date: August, 2023.                                                                  #
#                                                                                       #
# ===================================== COPYRIGHT ===================================== #

# ======= CITE OUR WORK ======= #
# You can cite our work with the following statement:
# IFRA-Cranfield (2023) ROS 2 Sim-to-Real Robot Control. URL: https://github.com/IFRA-Cranfield/ros2_SimRealRobotControl.
*/

// RobPose.cpp:

// Required to include ROS2 (C++):
#include "rclcpp/rclcpp.hpp"

// Required for timer:
#include <chrono>
#include <functional>
#include <memory>
#include <string>
using namespace std::chrono_literals;

// Include MoveIt!2:
#include <moveit/move_group_interface/move_group_interface_improved.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit_msgs/action/move_group.hpp>
#include <rclcpp_action/rclcpp_action.hpp>

// Include the Robpose ROS2 Message:
#include "ros2srrc_data/msg/robpose.hpp"

// Declaration of GLOBAL VARIABLE --> MoveIt!2 Interface:
moveit::planning_interface::MoveGroupInterface move_group_interface_ROB;

// Declaration of GLOBAL VARIABLE --> ROBOT PARAMETER:
std::string param_ROB = "none";
std::string param_ROB_GROUP = "none";

// Declaration of GLOBAL VARIABLE --> ROBOT POSE:
ros2srrc_data::msg::Robpose POSE; 

// =============================================================================== //
//  PARAM -> ROBOT:

class RobPose_PUB : public rclcpp::Node
{
public:
  RobPose_PUB()
  : Node("ros2srrc_RobPosePUB"), count_(0)
  {
    publisher_ = this->create_publisher<ros2srrc_data::msg::Robpose>("Robpose", 10);
    timer_ = this->create_wall_timer(50ms, std::bind(&RobPose_PUB::timer_callback, this));
  }

private:

  void timer_callback()
  {
    if (!move_group_interface_ROB.getRobotModel()) {
      return;
    }

    if (!move_group_interface_ROB.getCurrentState(0.5))
    {
        return;
    }

    auto CP_INFO = move_group_interface_ROB.getCurrentPose();

    POSE.x = CP_INFO.pose.position.x;
    POSE.y = CP_INFO.pose.position.y;
    POSE.z = CP_INFO.pose.position.z;
    POSE.qx = CP_INFO.pose.orientation.x;
    POSE.qy = CP_INFO.pose.orientation.y;
    POSE.qz = CP_INFO.pose.orientation.z;
    POSE.qw = CP_INFO.pose.orientation.w;

    publisher_->publish(POSE);

  }

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<ros2srrc_data::msg::Robpose>::SharedPtr publisher_;
  size_t count_;

};

// ===================================================================================== //
// ======================================= MAIN ======================================== //
// ===================================================================================== //

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<RobPose_PUB>();

  auto moveit_node = std::make_shared<rclcpp::Node>(
      "moveit_helper_node_robpose",
      rclcpp::NodeOptions()
          .automatically_declare_parameters_from_overrides(true)
  );

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(moveit_node);
  std::thread([&executor]() { executor.spin(); }).detach();

  // === PARAM ===
  node->declare_parameter("ROB_PARAM", "none");
  param_ROB = node->get_parameter("ROB_PARAM").as_string();

  RCLCPP_INFO(node->get_logger(), "ROB_PARAM received -> %s", param_ROB.c_str());

  node->declare_parameter("ROB_GROUP", "none");

  param_ROB_GROUP =
      node->get_parameter("ROB_GROUP").as_string();

  RCLCPP_INFO(
      node->get_logger(),
      "ROB_GROUP received -> %s",
      param_ROB_GROUP.c_str()
  );

  auto move_group_client =
      rclcpp_action::create_client<moveit_msgs::action::MoveGroup>(
          moveit_node,
          "move_action"
      );

  RCLCPP_INFO(
      node->get_logger(),
      "Waiting for MoveGroup action server..."
  );

  if (!move_group_client->wait_for_action_server(std::chrono::seconds(10)))
  {
      RCLCPP_ERROR(
          node->get_logger(),
          "MoveGroup action server not available!"
      );

      rclcpp::shutdown();
      return 1;
  }

  // === MOVEIT ===
  using moveit::planning_interface::MoveGroupInterface;

  move_group_interface_ROB =
      MoveGroupInterface(moveit_node, param_ROB_GROUP);

  move_group_interface_ROB.startStateMonitor();

  RCLCPP_INFO(
      node->get_logger(),
      "Waiting for current robot state..."
  );

  rclcpp::sleep_for(std::chrono::seconds(3));

  auto current_state =
      move_group_interface_ROB.getCurrentState(20.0);

  if (!current_state)
  {
      RCLCPP_ERROR(node->get_logger(), "Failed to get current robot state!");
      rclcpp::shutdown();
      return 1;
  }

  RCLCPP_INFO(
      node->get_logger(),
      "MoveGroupInterface ready for ROBOT group: %s",
      param_ROB_GROUP.c_str()
  );

  rclcpp::spin(node);

  rclcpp::shutdown();
  return 0;
}