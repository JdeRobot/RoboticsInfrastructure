#ifndef COMMON_INTERFACES_CPP__ODOMETRY_HPP_
#define COMMON_INTERFACES_CPP__ODOMETRY_HPP_

#include <vector>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "nav_msgs/msg/odometry.hpp"

struct Pose3d {
    double x, y, z, h, yaw, pitch, roll, timeStamp;
    std::vector<double> q;
    std::string to_string() const;
};

double quat2Yaw(double qw, double qx, double qy, double qz);
double quat2Pitch(double qw, double qx, double qy, double qz);
double quat2Roll(double qw, double qx, double qy, double qz);
Pose3d odometry2Pose3D(const nav_msgs::msg::Odometry& odom);

class OdometryNode : public rclcpp::Node {
public:
    OdometryNode(const std::string& topic, const std::string& node_name = "odometry_node");
    Pose3d getPose3d() const;

private:
    void listener_callback(const nav_msgs::msg::Odometry::SharedPtr msg);
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr sub_;
    nav_msgs::msg::Odometry last_pose_;
};

#endif