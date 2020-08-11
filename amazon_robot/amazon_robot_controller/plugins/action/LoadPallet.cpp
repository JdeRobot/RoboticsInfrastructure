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

#include "amazon_robot_controller/plugins/action/LoadPallet.hpp"
// #include "gazebo_msgs/apply_joint_effort.hpp"
// #include "behaviortree_cpp_v3/behavior_tree.h"
// #include "nav2_behavior_tree/bt_service_node.hpp"

namespace amazon_robot_controller
{

LoadPallet::LoadPallet(
  const std::string & xml_tag_name,
  const BT::NodeConfiguration & conf)
: BT::ActionNodeBase(xml_tag_name, conf), counter_(0)
{
  // std::shared_ptr<rclcpp::Node> node = rclcpp::Node::make_shared("add_two_ints_client");
  // rclcpp::Client<example_interfaces::srv::AddTwoInts>::SharedPtr client =
  // node->create_client<example_interfaces::srv::AddTwoInts>("add_two_ints");
}
// void
// LoadPallet::halt()
// {
//   std::cout << "LoadPallet halt" << std::endl;
// }
BT::NodeStatus LoadPallet::tick()
{
  std::vector<geometry_msgs::msg::PoseStamped> goals;

  std::cout << "LoadPallet tick " << counter_ << std::endl;


  if (counter_++ < 5) {
    return BT::NodeStatus::RUNNING;
  } else {
    counter_ = 0;
    return BT::NodeStatus::SUCCESS;
  }
}

}  // namespace amazon_robot_controller

#include "behaviortree_cpp_v3/bt_factory.h"
BT_REGISTER_NODES(factory)
{
  factory.registerNodeType<amazon_robot_controller::LoadPallet>("LoadPallet");
}
