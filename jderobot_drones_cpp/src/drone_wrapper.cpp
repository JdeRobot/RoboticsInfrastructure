#include "jderobot_drones_cpp/drone_wrapper.hpp"

DroneWrapper::DroneWrapper(const std::string &drone_id) : as2::Node(drone_id) {
  // QoS for sensors (best effort)
  auto qos_sensors = rclcpp::QoS(10).best_effort().volatile_durability();

  // Initialize reference handlers
  pos_handler_ = std::make_shared<as2::motionReferenceHandlers::PositionMotionHandler>(this);
  speed_handler_ = std::make_shared<as2::motionReferenceHandlers::SpeedMotionHandler>(this);

  // Subscriptions
  yaw_sub_ = this->create_subscription<geometry_msgs::msg::TwistStamped>(
      "self_localization/twist", qos_sensors,
      std::bind(&DroneWrapper::yawRateCb, this, std::placeholders::_1));

  // Service client for state events
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
  // Logical flow: Arm -> Offboard -> Takeoff Event
  this->arm();
  this->offboard();
  callStateEvent(as2_msgs::msg::PlatformStateMachineEvent::TAKE_OFF);
  
  // Block until height reached (simplified)
  while (std::abs(this->position_.z - height) > 0.25) {
    setCmdPos(position_.x, position_.y, height, 0.0);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }
  callStateEvent(as2_msgs::msg::PlatformStateMachineEvent::TOOK_OFF);
}

void DroneWrapper::callStateEvent(int8_t event) {
  auto request = std::make_shared<as2_msgs::srv::SetPlatformStateMachineEvent::Request>();
  request->event.event = event;
  state_client_->async_send_request(request);
}

void DroneWrapper::yawRateCb(const geometry_msgs::msg::TwistStamped::SharedPtr msg) {
  yaw_rate_ = msg->twist.angular.z;
}