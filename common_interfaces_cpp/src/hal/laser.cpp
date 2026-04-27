#include "common_interfaces_cpp/hal/laser.hpp"
#include <sstream>
#include <cmath>

const double PI = M_PI;

LaserData::LaserData() {
    minAngle = 0;  // Angle of first value (rads)
    maxAngle = 0;  // Angle of last value (rads)
    minRange = 0;  // Min Range possible (meters)
    maxRange = 0;  // Max Range possible (meters)
    timeStamp = 0; // seconds
}

std::string LaserData::to_string() const {
    std::ostringstream oss;
    oss << "LaserData: {\n   minAngle: " << minAngle
        << "\n   maxAngle: " << maxAngle
        << "\n   minRange: " << minRange
        << "\n   maxRange: " << maxRange
        << "\n   timeStamp: " << timeStamp
        << "\n   values: [";
    
    // Mimics Python's str(self.values) list printing
    for (size_t i = 0; i < values.size(); ++i) {
        oss << values[i];
        if (i < values.size() - 1) {
            oss << ", ";
        }
    }
    oss << "]\n}";
    
    return oss.str();
}

LaserData laserScan2LaserData(const sensor_msgs::msg::LaserScan& scan) {
    LaserData laser;
    laser.values = scan.ranges;
    
    /* ROS Angle Map      JdeRobot Angle Map
                0                  PI/2
                |                   |
                |                   |
       PI/2 --------- -PI/2  PI --------- 0
                |                   |
                |                   |
    */
    laser.minAngle = scan.angle_min + PI / 2.0;
    laser.maxAngle = scan.angle_max + PI / 2.0;
    laser.maxRange = scan.range_max;
    laser.minRange = scan.range_min;
    laser.timeStamp = scan.header.stamp.sec + (scan.header.stamp.nanosec * 1e-9);
    
    return laser;
}

LaserNode::LaserNode(const std::string& topic, const std::string& node_name) 
    : Node(node_name) {
    sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
        topic, 10, std::bind(&LaserNode::listener_callback, this, std::placeholders::_1)
    );
}

void LaserNode::listener_callback(const sensor_msgs::msg::LaserScan::SharedPtr scan) {
    last_scan_ = *scan;
}

LaserData LaserNode::getLaserData() const {
    return laserScan2LaserData(last_scan_);
}