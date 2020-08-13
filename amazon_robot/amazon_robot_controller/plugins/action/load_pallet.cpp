// Copyright 2019 Intelligent Robotics Lab
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// Modified By: Shreyas Gokhale <shreyas6gokhale@gmail.com>


#include <string>
#include <iostream>

#include "amazon_robot_controller/plugins/action/load_pallet.hpp"
// #include "gazebo_msgs/apply_joint_effort.hpp"
// #include "behaviortree_cpp_v3/behavior_tree.h"
// #include "nav2_behavior_tree/bt_service_node.hpp"

namespace amazon_robot_controller
{

LoadPallet::LoadPallet(
  const std::string & action_name,
  const BT::NodeConfiguration & conf)
: BT::ActionNodeBase(action_name, conf), counter_(0)
{
  load_pallet_node_ = config().blackboard->get<rclcpp::Node::SharedPtr>("load_node");
  load_pallet_client_ = config().blackboard->get<rclcpp::Client<gazebo_msgs::srv::ApplyJointEffort>::SharedPtr>("load_client");
  is_loaded_ = false; 

}

void
LoadPallet::halt()
{
  std::cout << "LoadPallet halt" << std::endl;
}

BT::NodeStatus LoadPallet::tick()
{

  std::vector<geometry_msgs::msg::PoseStamped> goals;

  std::cout << " LoadPallet Behaviour Called " << std::endl;
 
  if (!ApplyJointEffort()) {  
    std::cout << "Load / Unload of pallet failed!! Returning..."; 
  } else {
    std::cout << "Load / Unload of pallet successful. Returning...";  
  }

  return BT::NodeStatus::SUCCESS;

}

bool LoadPallet::ApplyJointEffort(){

  // auto joint_state = config().blackboard->get<rclcpp::Node::SharedPtr>("joint_state");
  std::cout << "Applying joint force"; 

  auto request = std::make_shared<gazebo_msgs::srv::ApplyJointEffort::Request>();
  // '{joint_name: "lift_joint", effort: -2.0, start_time: {sec: 0, nanosec: 0}, duration: {sec: 2000, nanosec: 0} }'

  request->joint_name = "lift_joint";
  request->start_time.sec = 0;
  request->duration.sec = 2000;

  if (is_loaded_ == true) 
  {
    request->effort = -4; 
    is_loaded_ = false;
    std::cout << "Unloaded Pallet"; 

  }
  else
  {
    is_loaded_ = true;
    request->effort = 3;
    std::cout << "Loaded Pallet"; 

  }
  
  while (!load_pallet_client_->wait_for_service(1s)) {
    if (!rclcpp::ok()) {
      RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Interrupted while waiting for the service. Exiting.");
    return false;
    }
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "service not available, waiting again...");
  }

  auto result = load_pallet_client_->async_send_request(request);
  // Wait for the result.
  if (rclcpp::spin_until_future_complete(load_pallet_node_, result) ==
    rclcpp::FutureReturnCode::SUCCESS)
  {
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Service Success!");

  } else {
    RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Failed to call service ApplyJointEffort");
    return false;
  }

  return true;
}

}  // namespace amazon_robot_controller

#include "behaviortree_cpp_v3/bt_factory.h"
BT_REGISTER_NODES(factory)
{
  factory.registerNodeType<amazon_robot_controller::LoadPallet>("LoadPallet");
}
