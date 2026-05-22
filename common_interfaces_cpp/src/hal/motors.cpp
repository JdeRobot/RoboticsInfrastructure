#include "common_interfaces_cpp/hal/motors.hpp"

MotorsNode::MotorsNode(const std::string& topic, double maxV, double maxW, const std::string& node_name) 
    : Node(node_name) {
    
    // maxV and maxW are kept in the constructor signature to match the Python interface
    
    pub = this->create_publisher<geometry_msgs::msg::Twist>(topic, 10);
}

void MotorsNode::sendV(double v) {
    last_twist.linear.x = v;
    pub->publish(last_twist);
}

void MotorsNode::sendW(double w) {
    last_twist.angular.z = w;
    pub->publish(last_twist);
}