#include "jderobot_drones_cpp/drone_wrapper.hpp"

DroneWrapper::DroneWrapper(const std::string &drone_id) : as2::Node(drone_id) {
  // QoS for sensors (best effort) and targets (transient local)
  auto qos_sensors = rclcpp::QoS(10).best_effort().durability_volatile();
  auto qos_targets = rclcpp::QoS(10).reliable().transient_local();

  // Initialize reference handlers
  pos_handler_ = std::make_shared<as2::motionReferenceHandlers::PositionMotion>(this);
  speed_handler_ = std::make_shared<as2::motionReferenceHandlers::SpeedMotion>(this);

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

  // Service clients for state events, arming and offboard
  state_client_ = this->create_client<as2_msgs::srv::SetPlatformStateMachineEvent>(
      "platform/state_machine_event");
      
  arm_client_ = this->create_client<std_srvs::srv::SetBool>("set_arming_state");
  offboard_client_ = this->create_client<std_srvs::srv::SetBool>("set_offboard_mode");
}

void DroneWrapper::setCmdPos(float x, float y, float z, float az) {
  // Send position command with yaw angle. The API requires 9 arguments including max velocities (vx, vy, vz).
  pos_handler_->sendPositionCommandWithYawAngle("earth", x, y, z, az, "base_link", 1.0f, 1.0f, 1.0f);
}

void DroneWrapper::setCmdVel(float vx, float vy, float vz, float az) {
  // Send speed command with yaw angle.
  speed_handler_->sendSpeedCommandWithYawSpeed("base_link", vx, vy, vz, az);
}

void DroneWrapper::takeoff(float height) {
  // Send arm command
  auto arm_req = std::make_shared<std_srvs::srv::SetBool::Request>();
  arm_req->data = true;
  arm_client_->async_send_request(arm_req);

  // Send offboard mode command
  auto offboard_req = std::make_shared<std_srvs::srv::SetBool::Request>();
  offboard_req->data = true;
  offboard_client_->async_send_request(offboard_req);

  // Send takeoff command and block until the drone reaches the target height
  callStateEvent(as2_msgs::msg::PlatformStateMachineEvent::TAKE_OFF);
  
  while (std::abs(this->position_.z - height) > 0.25) {
    setCmdPos(position_.x, position_.y, height, 0.0);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }
  
  // Take off finished
  callStateEvent(as2_msgs::msg::PlatformStateMachineEvent::TOOK_OFF);
}

void DroneWrapper::land() {
  // Send landing command
  callStateEvent(as2_msgs::msg::PlatformStateMachineEvent::LAND);
}

void DroneWrapper::callStateEvent(int8_t event) {
  // Request Aerostack to update state machine for the given event
  auto request = std::make_shared<as2_msgs::srv::SetPlatformStateMachineEvent::Request>();
  request->event.event = event;
  state_client_->async_send_request(request);
}

void DroneWrapper::yawRateCb(const geometry_msgs::msg::TwistStamped::SharedPtr msg) {
  // Update current yaw rate from subscription
  yaw_rate_ = msg->twist.angular.z;
}

void DroneWrapper::infoCb(const as2_msgs::msg::PlatformInfo::SharedPtr msg) {
  // Update current platform state
  state_ = msg->status.state;
}

void DroneWrapper::targetCb(const geometry_msgs::msg::PoseStamped::SharedPtr msg) {
  // Update target pose from target management
  target_pose_ = msg->pose;
}