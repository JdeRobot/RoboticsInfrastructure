#include <string>
#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"

class MotorsNode : public rclcpp::Node {
    /** ROS2 node that publishes linear and angular velocity commands to a robot. */
public:
    MotorsNode(const std::string& topic, const std::string& node_name, double maxV, double maxW) 
        : Node(node_name), maxV_(maxV), maxW_(maxW) {
        
        pub_ = this->create_publisher<geometry_msgs::msg::Twist>(topic, 10);
    }

    /** Publish a linear velocity command.
     * * Args:
     * v (float): Linear velocity in m/s.
     */
    void sendV(double v) {
        last_twist_.linear.x = v;
        pub_->publish(last_twist_);
    }

    /** Publish an angular velocity command.
     * * Args:
     * w (float): Angular velocity in rad/s.
     */
    void sendW(double w) {
        last_twist_.angular.z = w;
        pub_->publish(last_twist_);
    }

private:
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
    geometry_msgs::msg::Twist last_twist_;
    double maxV_;
    double maxW_;
};