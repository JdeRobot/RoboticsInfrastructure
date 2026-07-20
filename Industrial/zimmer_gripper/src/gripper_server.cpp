#include "zimmer_gripper/gripper_server.hpp"

#include <chrono>
#include <future>
#include <thread>

using namespace std::placeholders;

ZimmerGripperServer::ZimmerGripperServer()
: Node("zimmer_gripper_server")
{
  io_client_ =
      this->create_client<ur_msgs::srv::SetIO>(
          "/io_and_status_controller/set_io");

  while (!io_client_->wait_for_service(std::chrono::seconds(1))) {
    RCLCPP_INFO(
        this->get_logger(),
        "Esperando al servicio /io_and_status_controller/set_io...");
  }

  action_server_ = rclcpp_action::create_server<Gripper>(
      this,
      "zimmer_gripper",
      std::bind(&ZimmerGripperServer::handle_goal, this, _1, _2),
      std::bind(&ZimmerGripperServer::handle_cancel, this, _1),
      std::bind(&ZimmerGripperServer::handle_accepted, this, _1));

  RCLCPP_INFO(this->get_logger(), "Zimmer Gripper Server iniciado");
}

rclcpp_action::GoalResponse
ZimmerGripperServer::handle_goal(
    const rclcpp_action::GoalUUID &,
    std::shared_ptr<const Gripper::Goal>)
{
  RCLCPP_INFO(this->get_logger(), "Objetivo recibido");
  return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
}

rclcpp_action::CancelResponse
ZimmerGripperServer::handle_cancel(
    const std::shared_ptr<GoalHandleGripper>)
{
  RCLCPP_INFO(this->get_logger(), "Cancelación recibida");
  return rclcpp_action::CancelResponse::ACCEPT;
}

void ZimmerGripperServer::handle_accepted(
    const std::shared_ptr<GoalHandleGripper> goal_handle)
{
  std::thread(
      std::bind(
          &ZimmerGripperServer::execute,
          this,
          goal_handle))
      .detach();
}

void ZimmerGripperServer::execute(
    const std::shared_ptr<GoalHandleGripper> goal_handle)
{
  const auto goal = goal_handle->get_goal();

  auto result = std::make_shared<Gripper::Result>();

  bool ok;

  if (goal->open) {
    RCLCPP_INFO(this->get_logger(), "Abriendo gripper");
    ok = openGripper();
  } else {
    RCLCPP_INFO(this->get_logger(), "Cerrando gripper");
    ok = closeGripper();
  }

  result->success = ok;

  if (ok) {
    goal_handle->succeed(result);
  } else {
    goal_handle->abort(result);
  }
}

bool ZimmerGripperServer::setToolOutput(uint8_t pin, bool state)
{
  auto request = std::make_shared<ur_msgs::srv::SetIO::Request>();

  request->fun = ur_msgs::srv::SetIO::Request::FUN_SET_DIGITAL_OUT;
  request->pin = pin;
  request->state =
      state ?
      ur_msgs::srv::SetIO::Request::STATE_ON :
      ur_msgs::srv::SetIO::Request::STATE_OFF;

  auto future = io_client_->async_send_request(request);

  if (future.wait_for(std::chrono::seconds(2)) !=
      std::future_status::ready) {
    RCLCPP_ERROR(this->get_logger(), "Timeout llamando al servicio SetIO");
    return false;
  }

  return future.get()->success;
}

bool ZimmerGripperServer::openGripper()
{
  bool ok = true;

  ok &= setToolOutput(
      ur_msgs::srv::SetIO::Request::PIN_TOOL_DOUT1,
      false);

  ok &= setToolOutput(
      ur_msgs::srv::SetIO::Request::PIN_TOOL_DOUT0,
      true);

  return ok;
}

bool ZimmerGripperServer::closeGripper()
{
  bool ok = true;

  ok &= setToolOutput(
      ur_msgs::srv::SetIO::Request::PIN_TOOL_DOUT0,
      false);

  ok &= setToolOutput(
      ur_msgs::srv::SetIO::Request::PIN_TOOL_DOUT1,
      true);

  return ok;
}

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<ZimmerGripperServer>();

  rclcpp::spin(node);

  rclcpp::shutdown();

  return 0;
}