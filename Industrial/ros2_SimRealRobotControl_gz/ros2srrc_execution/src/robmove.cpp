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

// RobMove.cpp:

// Required to include ROS2 and ROS2 Action Server:
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

// Include the /Robmove ROS2 Action:
#include "ros2srrc_data/action/robmove.hpp"

// Include MoveIt!2:
#include <moveit/move_group_interface/move_group_interface_improved.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>

#include <moveit_msgs/action/move_group.hpp>

#include <moveit/trajectory_processing/iterative_time_parameterization.h>
#include <moveit/robot_trajectory/robot_trajectory.h>
#include <geometry_msgs/msg/pose.hpp>

// Declaration of GLOBAL VARIABLE --> MoveIt!2 Interface:
moveit::planning_interface::MoveGroupInterface move_group_interface_ROB;

// Declaration of GLOBAL VARIABLE --> ROBOT PARAMETER:
std::string param_ROB = "none";

// Declaration of GLOBAL VARIABLE --> RES:
std::string RES = "none";

// Declaration of GLOBAL VARIABLE --> ROBOT GROUP:
std::string param_ROB_GROUP = "none";

// =============================================================================== //
// MoveIt!2 -> MoveGroupInterface/Plan function:

moveit::planning_interface::MoveGroupInterface::Plan plan_ROB() {

    moveit::planning_interface::MoveGroupInterface::Plan my_plan;
    bool success = (move_group_interface_ROB.plan(my_plan) == moveit::planning_interface::MoveItErrorCode::SUCCESS);

    // Execute the plan
    if (success)
    {
        RES = "PLANNING: OK";
        return(my_plan);
    }
    else
    {
        RES = "PLANNING: ERROR";
        return(my_plan);
    }

};

// =============================================================================== //
// ROS2 Action Server to move the ROBOT:

class ActionServer : public rclcpp::Node
{

public:
    using Robmove = ros2srrc_data::action::Robmove;
    using GoalHandle = rclcpp_action::ServerGoalHandle<Robmove>;

    explicit ActionServer(const rclcpp::NodeOptions & options = rclcpp::NodeOptions()) : Node("ros2srrc_RobMove", options){

        this->declare_parameter("ROB_PARAM", "none");
        param_ROB = this->get_parameter("ROB_PARAM").as_string();
        RCLCPP_INFO(this->get_logger(), "ROB_PARAM received -> %s", param_ROB.c_str());

        this->declare_parameter("ROB_GROUP", "none");
        param_ROB_GROUP = this->get_parameter("ROB_GROUP").as_string();

        RCLCPP_INFO(
            this->get_logger(),
            "ROB_GROUP received -> %s",
            param_ROB_GROUP.c_str());

        action_server_ = rclcpp_action::create_server<Robmove>(
            this,
            "/Robmove",
            std::bind(&ActionServer::handle_goal, this, std::placeholders::_1, std::placeholders::_2),
            std::bind(&ActionServer::handle_cancel, this, std::placeholders::_1),
            std::bind(&ActionServer::handle_accepted, this, std::placeholders::_1)
            );

    }

private:
    rclcpp_action::Server<Robmove>::SharedPtr action_server_;

    rclcpp_action::GoalResponse handle_goal(const rclcpp_action::GoalUUID & uuid, std::shared_ptr<const Robmove::Goal> goal)
    {
        RCLCPP_INFO(get_logger(), "RobMove (/Robmove) -> RECEIVED A ROBOT MOVEMENT REQUEST:");
        RCLCPP_INFO(get_logger(), "Movement TYPE -> %s", goal->type.c_str());
        RCLCPP_INFO(get_logger(), "Movement SPEED -> %.2f", goal->speed);
        RCLCPP_INFO(get_logger(), "Desired POSITION -> (x: %.3f, y: %.3f, z: %.3f)", goal->x, goal->y, goal->z);
        RCLCPP_INFO(get_logger(), "DESIRED ORIENTATION -> (qx: %.3f, qy: %.3f, qz: %.3f, qw: %.3f)", goal->qx, goal->qy, goal->qz, goal->qw);
        return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
    }

    void handle_accepted(const std::shared_ptr<GoalHandle> goal_handle)
    {
        std::thread(
            [this, goal_handle]() {
                execute(goal_handle);
            }).detach();
    }

    rclcpp_action::CancelResponse handle_cancel(const std::shared_ptr<GoalHandle> goal_handle)
    {
        RCLCPP_INFO(this->get_logger(), "Received a cancel request.");
        move_group_interface_ROB.stop();
        (void)goal_handle;
        return rclcpp_action::CancelResponse::ACCEPT;
    }

    void execute(const std::shared_ptr<GoalHandle> goal_handle)
    {

        // 0. INFORMATION -> Current Robot Pose:
       auto CP_INFO = move_group_interface_ROB.getCurrentPose();

        auto state = move_group_interface_ROB.getCurrentState();
        state->update();

        const auto& tf = state->getGlobalLinkTransform("tool0");

        RCLCPP_INFO(get_logger(),
            "CURRENTPOSE = %.3f %.3f %.3f",
            CP_INFO.pose.position.x,
            CP_INFO.pose.position.y,
            CP_INFO.pose.position.z);

        RCLCPP_INFO(get_logger(),
            "STATE TOOL  = %.3f %.3f %.3f",
            tf.translation().x(),
            tf.translation().y(),
            tf.translation().z());

        // 1. OBTAIN INPUT PARAMETERS:
        const auto GOAL = goal_handle->get_goal();

        // 2. DECLARE RESULT:
        auto RESULT = std::make_shared<Robmove::Result>();

        // 3. Robot Movement -> EXECUTION:

        moveit::planning_interface::MoveGroupInterface::Plan MyPlan;

        auto CURRENT_POSE = move_group_interface_ROB.getCurrentPose();

        geometry_msgs::msg::Pose TARGET_POSE;
        TARGET_POSE.position.x = GOAL->x;
        TARGET_POSE.position.y = GOAL->y;
        TARGET_POSE.position.z = GOAL->z;
        TARGET_POSE.orientation.x = GOAL->qx;
        TARGET_POSE.orientation.y = GOAL->qy;
        TARGET_POSE.orientation.z = GOAL->qz;
        TARGET_POSE.orientation.w = GOAL->qw;

        RCLCPP_INFO(
            get_logger(),
            "TARGET POSE = %.3f %.3f %.3f",
            TARGET_POSE.position.x,
            TARGET_POSE.position.y,
            TARGET_POSE.position.z);

        move_group_interface_ROB.setPoseTarget(TARGET_POSE);

        const moveit::core::JointModelGroup* jmg =
            state->getJointModelGroup(param_ROB_GROUP);

        bool found_ik = state->setFromIK(jmg, TARGET_POSE);

        state->update();

        const auto& ik_tf = state->getGlobalLinkTransform("tool0");

        RCLCPP_INFO(
            get_logger(),
            "IK TOOL = %.3f %.3f %.3f",
            ik_tf.translation().x(),
            ik_tf.translation().y(),
            ik_tf.translation().z());

        RCLCPP_INFO(get_logger(), "IK FOUND = %d", found_ik);

        if (!found_ik)
        {
            RCLCPP_ERROR(get_logger(), "NO IK SOLUTION");
        }

        if (found_ik)
        {
            std::vector<double> vals;
            state->copyJointGroupPositions(jmg, vals);

            for (size_t i = 0; i < vals.size(); ++i)
                RCLCPP_INFO(get_logger(), "IK[%zu] = %.6f", i, vals[i]);
        }
        
        state->update();

        const auto &tf = state->getGlobalLinkTransform("tool0");

        RCLCPP_INFO(
            get_logger(),
            "IK TOOL = %.3f %.3f %.3f",
            tf.translation().x(),
            tf.translation().y(),
            tf.translation().z());

        move_group_interface_ROB.setStartStateToCurrentState();

        move_group_interface_ROB.setPlannerId(GOAL->type);
        move_group_interface_ROB.setMaxVelocityScalingFactor(GOAL->speed);

        // ===== DEBUG =====
        auto joints = move_group_interface_ROB.getCurrentJointValues();

        RCLCPP_INFO(get_logger(), "CURRENT JOINTS:");

        for (size_t i = 0; i < joints.size(); ++i)
        {
            RCLCPP_INFO(
                get_logger(),
                "CURRENT[%zu] = %.6f",
                i,
                joints[i]);
        }

        // Estado interno de MoveIt
        auto planning_state = move_group_interface_ROB.getCurrentState();

        std::vector<double> planning_vals;

        planning_state->copyJointGroupPositions(
            planning_state->getJointModelGroup(param_ROB_GROUP),
            planning_vals);

        RCLCPP_INFO(get_logger(), "PLANNING STATE:");

        for (size_t i = 0; i < planning_vals.size(); ++i)
        {
            RCLCPP_INFO(
                get_logger(),
                "STATE[%zu] = %.6f",
                i,
                planning_vals[i]);
        }
        // ==================

        MyPlan = plan_ROB();

        if (RES == "PLANNING: OK"){
            robot_trajectory::RobotTrajectory rt(
                move_group_interface_ROB.getRobotModel(),
                param_ROB_GROUP
            );

            moveit::core::RobotStatePtr current_state = move_group_interface_ROB.getCurrentState();

            rt.setRobotTrajectoryMsg(
                *current_state,
                MyPlan.trajectory_
            );

            trajectory_processing::IterativeParabolicTimeParameterization iptp;
            bool success = iptp.computeTimeStamps(rt, 1.0);

            if (!success) {
                RCLCPP_ERROR(this->get_logger(), "Time parameterization failed!");
            }

            rt.getRobotTrajectoryMsg(MyPlan.trajectory_);

            bool ExecSUCCESS = (move_group_interface_ROB.execute(MyPlan) == moveit::planning_interface::MoveItErrorCode::SUCCESS);

            auto end_joints = move_group_interface_ROB.getCurrentJointValues();

            RCLCPP_INFO(get_logger(), "FINAL JOINTS:");

            for (size_t i = 0; i < end_joints.size(); ++i)
            {
                RCLCPP_INFO(
                    get_logger(),
                    "FINAL[%zu] = %.6f",
                    i,
                    end_joints[i]);
            }

            if (goal_handle->is_canceling()) {
                RCLCPP_INFO(this->get_logger(), "ROBOT MOVEMENT (%s) has been CANCELED.", GOAL->type.c_str());
                RESULT->success = false;
                RESULT->message = "RobMove: CANCELED";
                goal_handle->canceled(RESULT);
                return;
            } 

            if (ExecSUCCESS){
                RCLCPP_INFO(this->get_logger(), "ROBOT MOVEMENT (%s) successfully executed.", GOAL->type.c_str());
                RESULT->success = true;
                RESULT->message = "RobMove: SUCCESS";
                goal_handle->succeed(RESULT);
            } else {
                RCLCPP_INFO(this->get_logger(), "ROBOT MOVEMENT (%s) failed. Reason -> EXECUTION failure.", GOAL->type.c_str());
                RESULT->success = false;
                RESULT->message = "RobMove: EXECUTION FAILED";
                goal_handle->succeed(RESULT);
            }

        } else {
            RCLCPP_INFO(this->get_logger(), "ROBOT MOVEMENT (%s) failed. Reason -> PLANNING failure.", GOAL->type.c_str());
            RESULT->success = false;
            RESULT->message = "RobMove: PLANNING FAILED";
            goal_handle->succeed(RESULT);
        }

        RES = "none";

        move_group_interface_ROB.setStartStateToCurrentState(); 

    }

};

// ===================================================================================== //
// ======================================= MAIN ======================================== //
// ===================================================================================== //

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto const logger = rclcpp::get_logger("RobMove_INTERFACE");

    auto node = std::make_shared<ActionServer>();

    // ===== MOVEIT HELPER NODE =====
    auto moveit_node = std::make_shared<rclcpp::Node>(
        "moveit_helper_node_robmove",
        rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true)
    );

    // Executor para que MoveIt funcione
    rclcpp::executors::SingleThreadedExecutor executor;
    executor.add_node(moveit_node);
    std::thread([&executor]() { executor.spin(); }).detach();

    auto move_group_client =
        rclcpp_action::create_client<moveit_msgs::action::MoveGroup>(
            node,
            "move_action"
        );

    RCLCPP_INFO(logger, "Waiting for MoveGroup action server...");

    if (!move_group_client->wait_for_action_server(std::chrono::seconds(10))) {
        RCLCPP_ERROR(logger, "MoveGroup action server not available!");
        rclcpp::shutdown();
        return 1;
    }

    RCLCPP_INFO(logger, "MoveGroup action server ready!");

    using moveit::planning_interface::MoveGroupInterface;

    move_group_interface_ROB =
    MoveGroupInterface(moveit_node, param_ROB_GROUP);

    move_group_interface_ROB.setMaxVelocityScalingFactor(1.0);
    move_group_interface_ROB.setMaxAccelerationScalingFactor(1.0);

    RCLCPP_INFO(
        logger,
        "MoveGroupInterface object created for ROBOT: %s",
        param_ROB_GROUP.c_str());

    rclcpp::spin(node);

    rclcpp::shutdown();
    return 0;
}