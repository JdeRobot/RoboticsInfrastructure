// Copyright (c) 2020  Shreyas Gokhale 
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



#ifndef AMAZON_ROBOT_CONTROLLER__PLUGINS__ACTION__LOAD_PALLET_HPP_
#define AMAZON_ROBOT_CONTROLLER__PLUGINS__ACTION__LOAD_PALLET_HPP_


#include <string>
#include <vector>
#include <chrono>


// #include "behaviortree_cpp_v3/behavior_tree.h"
// #include "behaviortree_cpp_v3/bt_factory.h"
#include "behaviortree_cpp_v3/action_node.h"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "gazebo_msgs/srv/apply_joint_effort.hpp"
#include "rclcpp/rclcpp.hpp"


namespace amazon_robot_controller {

    using namespace std::chrono_literals;

    class LoadPallet : public BT::ActionNodeBase {
    public:
        explicit LoadPallet(
                const std::string &action_name,
                const BT::NodeConfiguration &conf);

        LoadPallet() = delete;

        void halt() override;

        BT::NodeStatus tick() override;

        bool ApplyJointEffort(int load);

        static BT::PortsList providedPorts() {
            return {BT::InputPort <std::vector <int32_t>> (
                    "load_queue",
                            "Load / Unload sequence corresponding to poses")};
//                    BT::BidirectionalPort<bool>("goal_achieved", "Has the goal been achieved?"),
//                    BT::OutputPort<geometry_msgs::msg::PoseStamped>("goal", "Destination to plan to")};
        }

        bool is_loaded_ = false;
        bool waiting_for_finish_ = false;
        bool use_default_behaviour_ = false;
    private:
        int counter_;
        rclcpp::Client<gazebo_msgs::srv::ApplyJointEffort>::SharedPtr load_pallet_client_;
        rclcpp::Node::SharedPtr load_pallet_node_;
    };

}  // namespace amazon_robot_controller
#endif