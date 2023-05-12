// Copyright 2019 Intelligent Robotics Lab, 2020 Shreyas Gokhale
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

namespace amazon_robot_controller {

    LoadPallet::LoadPallet(
            const std::string &action_name,
            const BT::NodeConfiguration &conf)
            : BT::ActionNodeBase(action_name, conf), counter_(0) {
        load_pallet_node_ = config().blackboard->get<rclcpp::Node::SharedPtr>("load_node");
        load_pallet_client_ = config().blackboard->get<rclcpp::Client<gazebo_msgs::srv::ApplyJointEffort>::SharedPtr>(
                "load_client");
        is_loaded_ = false;

    }

    void
    LoadPallet::halt() {
        std::cout << "LoadPallet halt" << std::endl;
    }

    BT::NodeStatus LoadPallet::tick() {
        std::cout << " LoadPallet Behaviour Called " << std::endl;
        bool action_result_ = false;
        int load;
        int32_t current_load_queue_idx = config().blackboard->get<int32_t>("current_load_queue_idx");
        std::vector <int32_t> load_effort_queue_ = config().blackboard->get<std::vector<int32_t>>("load_queue");
//        !getInput("load_queue", load_effort_queue_)


        if (load_effort_queue_.size()<=1) {
            std::cout << " No LoadPallet messages found, using alternate Load and Unload " << std::endl;
            use_default_behaviour_ = true;
            load = 0;
        }
        else{
            load = load_effort_queue_[current_load_queue_idx];
            use_default_behaviour_ = false;

        }

        if (!waiting_for_finish_) {
            action_result_ = ApplyJointEffort(load);
            if (!action_result_) {
                std::cout << "Load / Unload of pallet failed!! Retrying...";
                waiting_for_finish_ = false;

            } else {
                std::cout << "Load / Unload of pallet successful. Returning...";
                waiting_for_finish_ = true;
                config().blackboard->set("current_load_queue_idx", current_load_queue_idx + 1);

            }
        }

        std::cout << "LoadPallet tick " << counter_ << std::endl;

//        return BT::NodeStatus::SUCCESS;


        if (counter_++ < 10) {
            return BT::NodeStatus::RUNNING;
        } else {
            counter_ = 0;
//            config().blackboard->set("current_load_queue_idx", current_load_queue_idx + 1);
            waiting_for_finish_ = false;
            return BT::NodeStatus::SUCCESS;

        }

    }

    bool LoadPallet::ApplyJointEffort(int load) {

        // auto joint_state = config().blackboard->get<rclcpp::Node::SharedPtr>("joint_state");
        std::cout << "Applying joint force" << std::endl;

        auto apply_joint_effort_request = std::make_shared<gazebo_msgs::srv::ApplyJointEffort::Request>();


        // '{joint_name: "lift_joint", effort: -2.0, start_time: {sec: 0, nanosec: 0}, duration: {sec: 2000, nanosec: 0} }'

        // ros2 service call /clear_joint_efforts gazebo_msgs/srv/JointRequest '{joint_name: "joint"}'

        apply_joint_effort_request->joint_name = "lift_joint";
        apply_joint_effort_request->start_time.sec = 0;
        apply_joint_effort_request->duration.sec = 2000;

        while (!load_pallet_client_->wait_for_service(2s)) {
            if (!rclcpp::ok()) {
                RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Interrupted while waiting for the service. Exiting.");
                return false;
            }
            RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "service not available, waiting again...");
        }

        if(use_default_behaviour_) {
            if (is_loaded_ == true) {
                apply_joint_effort_request->effort = -3;
                is_loaded_ = false;
                std::cout << "Unloaded Pallet";

            } else {
                is_loaded_ = true;
                apply_joint_effort_request->effort = 3;
                std::cout << "Loaded Pallet";

            }
        }
        else{
            apply_joint_effort_request->effort = load;
            std::cout << "Applying effort: " << load << std::endl;

            if (load>=2)
                is_loaded_ = true;
            else is_loaded_ = false;

        }

        auto result = load_pallet_client_->async_send_request(apply_joint_effort_request);
        // Wait for the result.
        if (rclcpp::spin_until_future_complete(load_pallet_node_, result) ==
            rclcpp::FutureReturnCode::SUCCESS) {
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
