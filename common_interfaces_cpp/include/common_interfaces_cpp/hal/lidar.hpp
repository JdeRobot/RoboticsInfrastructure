#ifndef COMMON_INTERFACES_CPP__LIDAR_HPP_
#define COMMON_INTERFACES_CPP__LIDAR_HPP_

#include <vector>
#include <string>
#include <memory>
#include <mutex>
#include <array>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"

class LidarData {
public:
    LidarData();
    std::vector<std::array<float, 3>> points;
    std::vector<float> intensities;
    double timeStamp;
    double min_range;
    double max_range;
    std::pair<double, double> field_of_view;
    bool is_dense;

    std::string to_string() const;
};

LidarData pointCloud2LidarData(const sensor_msgs::msg::PointCloud2::SharedPtr cloud);

class LidarNode : public rclcpp::Node {
public:
    LidarNode(const std::string& topic, const std::string& node_name = "lidar_node");
    LidarData getLidarData();
    sensor_msgs::msg::PointCloud2::SharedPtr get_point_cloud();

private:
    void pointcloud_callback(const sensor_msgs::msg::PointCloud2::SharedPtr cloud);

    std::mutex lock_;
    sensor_msgs::msg::PointCloud2::SharedPtr last_cloud_;
    rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_;
};

#endif