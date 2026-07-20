#include "zimmer_gripper/gripper_server.hpp"

#include <thread>

using namespace std::placeholders;

ZimmerGripperServer::ZimmerGripperServer()
: Node("zimmer_gripper_server")
{
    // Cliente del servicio SetIO
    io_client_ =
        this->create_client<ur_msgs::srv::SetIO>(
            "/io_and_status_controller/set_io");

    while (!io_client_->wait_for_service(std::chrono::seconds(1)))
    {
        RCLCPP_INFO(get_logger(),
                    "Esperando al servicio /io_and_status_controller/set_io...");
    }

    // Crear Action Server
    action_server_ = rclcpp_action::create_server<Gripper>(
        this,
        "zimmer_gripper",
        std::bind(&ZimmerGripperServer::handle_goal, this, _1, _2),
        std::bind(&ZimmerGripperServer::handle_cancel, this, _1),
        std::bind(&ZimmerGripperServer::handle_accepted, this, _1));

    RCLCPP_INFO(get_logger(), "Zimmer Gripper Action Server iniciado.");
}

rclcpp_action::GoalResponse
ZimmerGripperServer::handle_goal(
    const rclcpp_action::GoalUUID &,
    std::shared_ptr<const Gripper::Goal>)
{
    RCLCPP_INFO(get_logger(), "Nuevo objetivo recibido.");

    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
}

rclcpp_action::CancelResponse
ZimmerGripperServer::handle_cancel(
    const std::shared_ptr<GoalHandleGripper>)
{
    RCLCPP_INFO(get_logger(), "Cancelación recibida.");

    return rclcpp_action::CancelResponse::ACCEPT;
}

void ZimmerGripperServer::handle_accepted(
    const std::shared_ptr<GoalHandleGripper> goal_handle)
{
    std::thread(
        std::bind(&ZimmerGripperServer::execute,
                  this,
                  goal_handle))
        .detach();
}