#ifndef COMMON_INTERFACES_CPP__LASER_HPP_
#define COMMON_INTERFACES_CPP__LASER_HPP_

#include <vector>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

/* ### AUXILIARY FUNCTIONS */

class LaserData {
public:
    LaserData();
    std::vector<float> values;  // meters
    double minAngle;            // Angle of first value (rads)
    double maxAngle;            // Angle of last value (rads)
    double minRange;            // Min Range possible (meters)
    double maxRange;            // Max Range possible (meters)
    double timeStamp;           // seconds

    std::string to_string() const;
};

/*
 * Translates from ROS LaserScan to JderobotTypes LaserData.
 * @param scan: ROS LaserScan to translate
 * @type scan: LaserScan
 * @return a LaserData translated from scan
 */
LaserData laserScan2LaserData(const sensor_msgs::msg::LaserScan& scan);


/* ### HAL INTERFACE ### */
class LaserNode : public rclcpp::Node {
public:
    LaserNode(const std::string& topic, const std::string& node_name = "laser_node");
    LaserData getLaserData() const;

private:
    void listener_callback(const sensor_msgs::msg::LaserScan::SharedPtr scan);
    
    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr sub_;
    sensor_msgs::msg::LaserScan last_scan_;
};

#endif