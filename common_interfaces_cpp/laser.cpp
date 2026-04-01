#include <vector>
#include <string>
#include <sstream>
#include <cmath>
#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

const double PI = M_PI;

struct LaserData {
    std::vector<float> values;
    double minAngle = 0.0;
    double maxAngle = 0.0;
    double minRange = 0.0;
    double maxRange = 0.0;
    double timeStamp = 0.0;

    std::string to_string() const {
        std::ostringstream oss;
        oss << "LaserData: {\n   minAngle: " << minAngle
            << "\n   maxAngle: " << maxAngle
            << "\n   minRange: " << minRange
            << "\n   maxRange: " << maxRange
            << "\n   timeStamp: " << timeStamp
            << "\n   values: [";
        for (size_t i = 0; i < values.size(); ++i) {
            oss << values[i];
            if (i != values.size() - 1) oss << ", ";
        }
        oss << "]\n}";
        return oss.str();
    }
};

LaserData laserScan2LaserData(const sensor_msgs::msg::LaserScan& scan) {
    LaserData laser;
    laser.values = scan.ranges;
    laser.minAngle = scan.angle_min + PI / 2.0;
    laser.maxAngle = scan.angle_max + PI / 2.0;
    laser.maxRange = scan.range_max;
    laser.minRange = scan.range_min;
    laser.timeStamp = scan.header.stamp.sec + (scan.header.stamp.nanosec * 1e-9);
    return laser;
}

class LaserNode : public rclcpp::Node {
public:
    LaserNode(const std::string& topic, const std::string& node_name) : Node(node_name) {
        sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
            topic, 10, std::bind(&LaserNode::listener_callback, this, std::placeholders::_1)
        );
    }

    LaserData getLaserData() const {
        return laserScan2LaserData(last_scan_);
    }

private:
    void listener_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg) {
        last_scan_ = *msg;
    }

    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr sub_;
    sensor_msgs::msg::LaserScan last_scan_;
};