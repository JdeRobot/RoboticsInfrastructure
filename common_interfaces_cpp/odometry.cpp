#include <string>
#include <vector>
#include <sstream>
#include <cmath>
#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "nav_msgs/msg/odometry.hpp"

const double PI = M_PI;

// AUXILIARY FUNCTIONS

/** Represents a 3D pose with position, orientation, and timestamp. */
struct Pose3d {
    double x = 0.0;     // X coord [meters]
    double y = 0.0;     // Y coord [meters]
    double z = 0.0;     // Z coord [meters]
    double h = 1.0;     // H param
    double yaw = 0.0;   // Yaw angle[rads]
    double pitch = 0.0; // Pitch angle[rads]
    double roll = 0.0;  // Roll angle[rads]
    std::vector<double> q = {0.0, 0.0, 0.0, 0.0};  // Quaternion
    double timeStamp = 0.0; // Time stamp [s]

    std::string to_string() const {
        std::ostringstream oss;
        oss << "Pose3D: {\n   x: " << x << "\n   y: " << y
            << "\n   z: " << z << "\n   H: " << h
            << "\n   Yaw: " << yaw << "\n   Pitch: " << pitch
            << "\n   Roll: " << roll
            << "\n   quaternion: [" << q[0] << ", " << q[1] << ", " << q[2] << ", " << q[3] << "]"
            << "\n   timeStamp: " << timeStamp << "\n}";
        return oss.str();
    }
};

/**
 * Translates from Quaternion to Yaw.
 * @param qw,qx,qy,qz: Quaternion values
 * @type qw,qx,qy,qz: float
 * @return Yaw value translated from Quaternion
 */
double quat2Yaw(double qw, double qx, double qy, double qz) {
    double rotateZa0 = 2.0 * (qx * qy + qw * qz);
    double rotateZa1 = qw * qw + qx * qx - qy * qy - qz * qz;
    double rotateZ = 0.0;
    if (rotateZa0 != 0.0 && rotateZa1 != 0.0) {
        rotateZ = std::atan2(rotateZa0, rotateZa1);
    }
    return rotateZ;
}

/**
 * Translates from Quaternion to Pitch.
 * @param qw,qx,qy,qz: Quaternion values
 * @type qw,qx,qy,qz: float
 * @return Pitch value translated from Quaternion
 */
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

/**
 * Translates from Quaternion to Roll.
 * @param qw,qx,qy,qz: Quaternion values
 * @type qw,qx,qy,qz: float
 * @return Roll value translated from Quaternion
 */
double quat2Roll(double qw, double qx, double qy, double qz) {
    double rotateXa0 = 2.0 * (qy * qz + qw * qx);
    double rotateXa1 = qw * qw - qx * qx - qy * qy + qz * qz;
    double rotateX = 0.0;

    if (rotateXa0 != 0.0 && rotateXa1 != 0.0) {
        rotateX = std::atan2(rotateXa0, rotateXa1);
    }
    return rotateX;
}

/**
 * Translates from ROS Odometry to JderobotTypes Pose3d.
 * @param odom: ROS Odometry to translate
 * @type odom: Odometry
 * @return a Pose3d translated from odom
 */
Pose3d odometry2Pose3D(const nav_msgs::msg::Odometry& odom) {
    Pose3d pose;
    auto ori = odom.pose.pose.orientation;

    pose.x = odom.pose.pose.position.x;
    pose.y = odom.pose.pose.position.y;
    pose.z = odom.pose.pose.position.z;
    // pose.h = odom.pose.pose.position.h
    pose.yaw = quat2Yaw(ori.w, ori.x, ori.y, ori.z);
    pose.pitch = quat2Pitch(ori.w, ori.x, ori.y, ori.z);
    pose.roll = quat2Roll(ori.w, ori.x, ori.y, ori.z);
    pose.q = {ori.w, ori.x, ori.y, ori.z};
    pose.timeStamp = odom.header.stamp.sec + (odom.header.stamp.nanosec * 1e-9);

    return pose;
}

// HAL INTERFACE 
class OdometryNode : public rclcpp::Node {
public:
    OdometryNode(const std::string& topic, const std::string& node_name = "odometry_node") 
        : Node(node_name) {
        sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
            topic, 10, std::bind(&OdometryNode::listener_callback, this, std::placeholders::_1)
        );
    }

    /**
     * Return the latest pose as a Pose3d object.
     *
     * Returns:
     * Pose3d with position, orientation, and timestamp fields populated.
     */
    Pose3d getPose3d() const {
        return odometry2Pose3D(last_pose_);
    }

private:
    /** Store the latest odometry message received from the topic. */
    void listener_callback(const nav_msgs::msg::Odometry::SharedPtr msg) {
        last_pose_ = *msg;
    }

    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr sub_;
    nav_msgs::msg::Odometry last_pose_;
};