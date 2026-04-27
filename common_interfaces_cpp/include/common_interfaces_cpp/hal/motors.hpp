#ifndef COMMON_INTERFACES_CPP__MOTORS_HPP_
#define COMMON_INTERFACES_CPP__MOTORS_HPP_

#include <string>
#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"

/* ### HAL INTERFACE ### */

/* ROS2 node that publishes linear and angular velocity commands to a robot. */
class MotorsNode : public rclcpp::Node {
public:
    MotorsNode(const std::string& topic, double maxV, double maxW, const std::string& node_name = "motors_node");

    /* Publish a linear velocity command.
     *
     * Args:
     * v (float): Linear velocity in m/s.
     */
    void sendV(double v);

    /* Publish an angular velocity command.
     *
     * Args:
     * w (float): Angular velocity in rad/s.
     */
    void sendW(double w);

private:
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub;
    geometry_msgs::msg::Twist last_twist;
};

#endif