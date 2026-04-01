#include "common_interfaces_cpp/odometry.hpp"
#include <sstream>
#include <cmath>

const double PI = M_PI;

std::string Pose3d::to_string() const {
    // ... tu código original ...
}

double quat2Yaw(double qw, double qx, double qy, double qz) {
    // ... tu código original ...
}

// ... resto de implementaciones exactas que ya tienes ...

OdometryNode::OdometryNode(const std::string& topic, const std::string& node_name) 
    : Node(node_name) {
    sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
        topic, 10, std::bind(&OdometryNode::listener_callback, this, std::placeholders::_1)
    );
}

Pose3d OdometryNode::getPose3d() const {
    return odometry2Pose3D(last_pose_);
}

void OdometryNode::listener_callback(const nav_msgs::msg::Odometry::SharedPtr msg) {
    last_pose_ = *msg;
}