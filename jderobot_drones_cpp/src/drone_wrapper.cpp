#include "jderobot_drones_cpp/drone_wrapper.hpp"

#include <chrono>
#include <cmath>
#include <thread>

using namespace std::chrono_literals;

// Constructor

DroneWrapper::DroneWrapper(const std::string &drone_id)
    : as2::Node(drone_id + "_wrapper", drone_id)
{
  // QoS profiles matching the Python wrapper
  auto qos_sensors = rclcpp::QoS(10).best_effort().durability_volatile();
  auto qos_targets = rclcpp::QoS(10).reliable().transient_local();

  // Dedicated callback group for service clients.
  // MutuallyExclusive means rclcpp::spin_until_future_complete() can process
  // service responses without conflicting with the external executor that spins
  // the subscription callbacks.
  service_cb_group_ = this->create_callback_group(
      rclcpp::CallbackGroupType::MutuallyExclusive);

  // Motion-reference handlers
  pos_handler_           = std::make_shared<as2::motionReferenceHandlers::PositionMotion>(this);
  speed_handler_         = std::make_shared<as2::motionReferenceHandlers::SpeedMotion>(this);
  speed_in_plane_handler_ = std::make_shared<as2::motionReferenceHandlers::SpeedInAPlaneMotion>(this);

  // Subscriptions
  yaw_sub_ = this->create_subscription<geometry_msgs::msg::TwistStamped>(
      "self_localization/twist", qos_sensors,
      std::bind(&DroneWrapper::yawRateCb, this, std::placeholders::_1));

  info_sub_ = this->create_subscription<as2_msgs::msg::PlatformInfo>(
      "platform/info", qos_sensors,
      std::bind(&DroneWrapper::infoCb, this, std::placeholders::_1));

  target_sub_ = this->create_subscription<geometry_msgs::msg::PoseStamped>(
      "target_management/pose", qos_targets,
      std::bind(&DroneWrapper::targetCb, this, std::placeholders::_1));

  pose_sub_ = this->create_subscription<geometry_msgs::msg::PoseStamped>(
      "self_localization/pose", qos_sensors,
      std::bind(&DroneWrapper::poseCb, this, std::placeholders::_1));

  // Service clients — assigned to the dedicated callback group
  state_client_ = this->create_client<as2_msgs::srv::SetPlatformStateMachineEvent>(
      "platform/state_machine_event",
      rmw_qos_profile_services_default,
      service_cb_group_);

  arm_client_ = this->create_client<std_srvs::srv::SetBool>(
      "set_arming_state",
      rmw_qos_profile_services_default,
      service_cb_group_);

  offboard_client_ = this->create_client<std_srvs::srv::SetBool>(
      "set_offboard_mode",
      rmw_qos_profile_services_default,
      service_cb_group_);
}

// Motion commands

void DroneWrapper::setCmdPos(float x, float y, float z, float az)
{
  pos_handler_->sendPositionCommandWithYawAngle(
      std::string("earth"), x, y, z, az,
      std::string("base_link"), 1.0f, 1.0f, 1.0f);
}

void DroneWrapper::setCmdVel(float vx, float vy, float vz, float az)
{
  speed_handler_->sendSpeedCommandWithYawSpeed(
      std::string("base_link"), vx, vy, vz, az);
}

void DroneWrapper::setCmdMix(float vx, float vy, float z, float az)
{
  // Use message-based overload to avoid ambiguous template resolution
  geometry_msgs::msg::PoseStamped pose_msg;
  pose_msg.header.frame_id = "earth";
  pose_msg.pose.position.z = z;

  geometry_msgs::msg::TwistStamped twist_msg;
  twist_msg.header.frame_id  = "base_link";
  twist_msg.twist.linear.x   = vx;
  twist_msg.twist.linear.y   = vy;
  twist_msg.twist.angular.z  = az;

  speed_in_plane_handler_->sendSpeedInAPlaneCommandWithYawSpeed(pose_msg, twist_msg);
}

// Blocking service helpers

void DroneWrapper::callSetBoolSync(
    rclcpp::Client<std_srvs::srv::SetBool>::SharedPtr client, bool value)
{
  // Wait until the service is available
  while (!client->wait_for_service(1s)) {
    RCLCPP_INFO(this->get_logger(), "Waiting for service '%s'...",
                client->get_service_name());
  }

  auto request  = std::make_shared<std_srvs::srv::SetBool::Request>();
  request->data = value;
  auto future   = client->async_send_request(request);

  // Spin *only* the service callback group until the future is ready.
  // This does not interfere with the MultiThreadedExecutor running elsewhere.
  rclcpp::executors::SingleThreadedExecutor tmp_exec;
  tmp_exec.add_node(this->get_node_base_interface());
  while (future.wait_for(10ms) != std::future_status::ready) {
    tmp_exec.spin_some();
  }
}

void DroneWrapper::callStateEventSync(int8_t event)
{
  while (!state_client_->wait_for_service(1s)) {
    RCLCPP_INFO(this->get_logger(), "Waiting for state_machine_event service...");
  }

  auto request         = std::make_shared<as2_msgs::srv::SetPlatformStateMachineEvent::Request>();
  request->event.event = event;
  auto future          = state_client_->async_send_request(request);

  rclcpp::executors::SingleThreadedExecutor tmp_exec;
  tmp_exec.add_node(this->get_node_base_interface());
  while (future.wait_for(10ms) != std::future_status::ready) {
    tmp_exec.spin_some();
  }

  auto result = future.get();
  RCLCPP_INFO(this->get_logger(), "State event sent — success: %s, current_state: %d",
              result->success ? "true" : "false",
              static_cast<int>(result->current_state));
}

// High-level takeoff / land

void DroneWrapper::takeoff(float height)
{
  // Guard: skip if already airborne
  if (state_ == 2 /* TAKING_OFF */ || state_ == 3 /* FLYING */) {
    RCLCPP_INFO(this->get_logger(), "Drone is already flying!");
    return;
  }

  // 1. Arm and switch to offboard mode — both must complete before continuing
  callSetBoolSync(arm_client_,      true);
  callSetBoolSync(offboard_client_, true);

  // 2. Request TAKE_OFF state transition and wait for acknowledgement
  callStateEventSync(as2_msgs::msg::PlatformStateMachineEvent::TAKE_OFF);

  // 3. Send position commands until the drone reaches the target height
  while (std::abs(position_.z - height) > 0.25f) {
    setCmdPos(position_.x, position_.y, height, orientation_.z);
    std::this_thread::sleep_for(100ms);
  }

  // 4. Confirm take-off is finished
  callStateEventSync(as2_msgs::msg::PlatformStateMachineEvent::TOOK_OFF);
}

void DroneWrapper::land()
{
  // Guard: skip if already on the ground
  if (state_ == 1 /* LANDED */ || state_ == 4 /* LANDING */) {
    RCLCPP_INFO(this->get_logger(), "Drone is already landed!");
    return;
  }

  // 1. Request LAND state transition
  callStateEventSync(as2_msgs::msg::PlatformStateMachineEvent::LAND);

  float start_height = position_.z;

  // 2. Descend until vertical speed drops (drone touched ground)
  while (true) {
    setCmdVel(0.0f, 0.0f, -0.5f, 0.0f);
    std::this_thread::sleep_for(100ms);

    // Same detection logic as Python: vz low AND meaningful height drop
    if (std::abs(speed_.z) < 0.1f &&
        std::abs(position_.z - start_height) > 0.1f) {
      break;
    }
  }

  // 3. Confirm landing and disarm
  callStateEventSync(as2_msgs::msg::PlatformStateMachineEvent::LANDED);
  callSetBoolSync(arm_client_, false);
}

// Subscription callbacks

void DroneWrapper::yawRateCb(const geometry_msgs::msg::TwistStamped::SharedPtr msg)
{
  yaw_rate_ = msg->twist.angular.z;

  // Also capture linear velocity from the same topic (same as Python wrapper)
  speed_.x = msg->twist.linear.x;
  speed_.y = msg->twist.linear.y;
  speed_.z = msg->twist.linear.z;
}

void DroneWrapper::infoCb(const as2_msgs::msg::PlatformInfo::SharedPtr msg)
{
  state_ = msg->status.state;
}

void DroneWrapper::targetCb(const geometry_msgs::msg::PoseStamped::SharedPtr msg)
{
  target_pose_ = msg->pose;
}

void DroneWrapper::poseCb(const geometry_msgs::msg::PoseStamped::SharedPtr msg)
{
  position_.x = msg->pose.position.x;
  position_.y = msg->pose.position.y;
  position_.z = msg->pose.position.z;

  // Convert quaternion → Roll / Pitch / Yaw
  tf2::Quaternion q(
      msg->pose.orientation.x,
      msg->pose.orientation.y,
      msg->pose.orientation.z,
      msg->pose.orientation.w);
  tf2::Matrix3x3 m(q);

  double roll, pitch, yaw;
  m.getRPY(roll, pitch, yaw);

  orientation_.x = roll;
  orientation_.y = pitch;
  orientation_.z = yaw;
}