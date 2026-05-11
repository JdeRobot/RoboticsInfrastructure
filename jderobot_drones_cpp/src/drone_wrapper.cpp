#include "jderobot_drones_cpp/drone_wrapper.hpp"

DroneWrapper::DroneWrapper(const std::string &drone_id) : as2::Node(drone_id) {
  auto qos_sensors = rclcpp::QoS(10).best_effort().durability_volatile();
  auto qos_targets = rclcpp::QoS(10).reliable().transient_local();

  pos_handler_ = std::make_shared<as2::motionReferenceHandlers::PositionMotion>(this);
  speed_handler_ = std::make_shared<as2::motionReferenceHandlers::SpeedMotion>(this);

  yaw_sub_ = this->create_subscription<geometry_msgs::msg::TwistStamped>(
      "self_localization/twist", qos_sensors,
      std::bind(&DroneWrapper::yawRateCb, this, std::placeholders::_1));

  info_sub_ = this->create_subscription<as2_msgs::msg::PlatformInfo>(
      "platform/info", qos_sensors,
      std::bind(&DroneWrapper::infoCb, this, std::placeholders::_1));

  target_sub_ = this->create_subscription<geometry_msgs::msg::PoseStamped>(
      "target_management/pose", qos_targets,
      std::bind(&DroneWrapper::targetCb, this, std::placeholders::_1));

  state_client_ = this->create_client<as2_msgs::srv::SetPlatformStateMachineEvent>(
      "platform/state_machine_event");
}

void DroneWrapper::setCmdPos(float x, float y, float z, float az) {
  pos_handler_->sendPositionCommandWithYawAngle("earth", x, y, z, az, "base_link", 1.0f);
}

void DroneWrapper::setCmdVel(float vx, float vy, float vz, float az) {
  speed_handler_->sendSpeedCommandWithYawSpeed("base_link", vx, vy, vz, az);
}

void DroneWrapper::takeoff(float height) {
  this->arm();
  this->offboard();
  callStateEvent(as2_msgs::msg::PlatformStateMachineEvent::TAKE_OFF);
  
  while (std::abs(this->position_.z - height) > 0.25) {
    setCmdPos(position_.x, position_.y, height, 0.0);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }
  callStateEvent(as2_msgs::msg::PlatformStateMachineEvent::TOOK_OFF);
}

void DroneWrapper::land() {
  callStateEvent(as2_msgs::msg::PlatformStateMachineEvent::LAND);
}

void DroneWrapper::callStateEvent(int8_t event) {
  auto request = std::make_shared<as2_msgs::srv::SetPlatformStateMachineEvent::Request>();
  request->event.event = event;
  state_client_->async_send_request(request);
}

void DroneWrapper::yawRateCb(const geometry_msgs::msg::TwistStamped::SharedPtr msg) {
  yaw_rate_ = msg->twist.angular.z;
}

void DroneWrapper::infoCb(const as2_msgs::msg::PlatformInfo::SharedPtr msg) {
  state_ = msg->status.state;
}

void DroneWrapper::targetCb(const geometry_msgs::msg::PoseStamped::SharedPtr msg) {
  target_pose_ = msg->pose;
}