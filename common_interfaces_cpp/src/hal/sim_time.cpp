#include "common_interfaces_cpp/sim_time.hpp"
#include <sstream>

SimTimeData::SimTimeData() {
    seconds = 0;
    nanoseconds = 0;
}

std::string SimTimeData::to_string() const {
    std::ostringstream oss;
    oss << "SimTimeData: {\n   sec: " << seconds
        << "\n   nanosec: " << nanoseconds;
    return oss.str();
}

SimTimeData simTime2SimTimeData(const rosgraph_msgs::msg::Clock& clock) {
    SimTimeData clockData;
    clockData.seconds = clock.clock.sec;
    clockData.nanoseconds = clock.clock.nanosec;
    return clockData;
}

SimTimeNode::SimTimeNode() 
    : Node("simulation_time_node") {
    
    rclcpp::QoS qos_policy(rclcpp::KeepLast(1));
    qos_policy.best_effort();

    sub = this->create_subscription<rosgraph_msgs::msg::Clock>(
        "/clock", 
        qos_policy, 
        std::bind(&SimTimeNode::listener_callback, this, std::placeholders::_1)
    );
}

void SimTimeNode::listener_callback(const rosgraph_msgs::msg::Clock::SharedPtr msg) {
    last_sim_time_ = *msg;
}

SimTimeData SimTimeNode::getSimTime() const {
    return simTime2SimTimeData(last_sim_time_);
}