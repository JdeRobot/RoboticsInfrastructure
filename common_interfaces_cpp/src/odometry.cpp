#include "common_interfaces_cpp/odometry.hpp"
#include <sstream>
#include <cmath>

const double PI = M_PI;

std::string Pose3d::to_string() const {
    std::ostringstream oss;
    oss << "Pose3D: {\n   x: " << x << "\n   y: " << y
        << "\n   z: " << z << "\n   H: " << h
        << "\n   Yaw: " << yaw << "\n   Pitch: " << pitch
        << "\n   Roll: " << roll
        << "\n   quaternion: [" << q[0] << ", " << q[1] << ", " << q[2] << ", " << q[3] << "]"
        << "\n   timeStamp: " << timeStamp << "\n}";
    return oss.str();
}

double quat2Yaw(double qw, double qx, double qy, double qz) {
    double rotateZa0 = 2.0 * (qx * qy + qw * qz);
    double rotateZa1 = qw * qw + qx * qx - qy * qy - qz * qz;
    double rotateZ = 0.0;
    if (rotateZa0 != 0.0 && rotateZa1 != 0.0) {
        rotateZ = std::atan2(rotateZa0, rotateZa1);
    }
    return rotateZ;
}

double quat2Pitch(double qw, double qx, double qy, double qz) {
    double rotateYa0 = -2.0 * (qx * qz - qw * qy);
    double rotateY = 0.0;
    if (rotateYa0 >= 1.0) {
        rotateY = PI / 2.0;
    } else if (rotateYa0 <= -1.0) {
        rotateY = -PI / 2.0;
    } else {
        rotateY = std::asin(rotateYa0);
    }
    return rotateY;
}

double quat2Roll(double qw, double qx, double qy, double qz) {
    double rotateXa0 = 2.0 * (qy * qz + qw * qx);
    double rotateXa1 = qw * qw - qx * qx - qy * qy + qz * qz;
    double rotateX = 0.0;

    if (rotateXa0 != 0.0 && rotateXa1 != 0.0) {
        rotateX = std::atan2(rotateXa0, rotateXa1);
    }
    return rotateX;
}

Pose3d odometry2Pose3D(const nav_msgs::msg::Odometry& odom) {
    Pose3d pose;
    auto ori = odom.pose.pose.orientation;

    pose.x = odom.pose.pose.position.x;
    pose.y = odom.pose.pose.position.y;
    pose.z = odom.pose.pose.position.z;
    pose.yaw = quat2Yaw(ori.w, ori.x, ori.y, ori.z);
    pose.pitch = quat2Pitch(ori.w, ori.x, ori.y, ori.z);
    pose.roll = quat2Roll(ori.w, ori.x, ori.y, ori.z);
    pose.q = {ori.w, ori.x, ori.y, ori.z};
    pose.timeStamp = odom.header.stamp.sec + (odom.header.stamp.nanosec * 1e-9);

    return pose;
}

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