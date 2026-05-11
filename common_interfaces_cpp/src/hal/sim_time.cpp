#include "common_interfaces_cpp/hal/sim_time.hpp"
#include <sstream>

SimTimeData::SimTimeData() {
    seconds = 0;
    nanoseconds = 0;
}

std::string SimTimeData::to_string() const {
    std::ostringstream oss;
    oss << "SimTimeData: {\n   sec: " << seconds
        << "\n   nanosec: " << nanoseconds << "\n}";
    return oss.str();
}

double SimTimeData::to_double() const {
    return static_cast<double>(seconds) + (static_cast<double>(nanoseconds) * 1e-9);
}

SimTimeData simTime2SimTimeData(const rosgraph_msgs::msg::Clock& clock) {
    SimTimeData clockData;
    clockData.seconds = clock.clock.sec;
    clockData.nanoseconds = clock.clock.nanosec;
    return clockData;
}

SimTimeNode::SimTimeNode(const std::string& node_name) 
    : Node(node_name) {
    
    rclcpp::QoS qos_policy(rclcpp::KeepLast(1));
    qos_policy.best_effort();

    sub = this->create_subscription<rosgraph_msgs::msg::Clock>(
        "/clock", 
        qos_policy, 
        std::bind(&SimTimeNode::listener_callback, this, std::placeholders::_1)
    );
}

void SimTimeNode::listener_callback(const rosgraph_msgs::msg::Clock::SharedPtr msg) {
    std::lock_guard<std::mutex> guard(lock_);
    last_sim_time_ = *msg;
}

SimTimeData SimTimeNode::getSimTime() {
    std::lock_guard<std::mutex> guard(lock_);
    return simTime2SimTimeData(last_sim_time_);
}