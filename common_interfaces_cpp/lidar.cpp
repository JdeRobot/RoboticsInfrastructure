#include <vector>
#include <string>
#include <sstream>
#include <cmath>
#include <memory>
#include <mutex>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "sensor_msgs/point_cloud2_iterator.hpp"

const double PI = M_PI;

struct Point3D {
    float x;
    float y;
    float z;
};

struct LidarData {
    std::vector<Point3D> points;
    std::vector<float> intensities;
    double timeStamp = 0.0;
    double min_range = 0.1;
    double max_range = 15.0;
    std::pair<double, double> field_of_view = {2.0 * PI / 3.0, PI / 18.0};
    bool is_dense = true;

    std::string to_string() const {
        std::ostringstream oss;
        oss << "LiDARData:\n"
            << "  timestamp: " << timeStamp << "\n"
            << "  points: " << points.size() << "\n"
            << "  range: [" << min_range << ", " << max_range << "]\n"
            << "  FOV: (" << field_of_view.first << ", " << field_of_view.second << ")\n"
            << "  is_dense: " << (is_dense ? "True" : "False");
        return oss.str();
    }
};

LidarData pointCloud2LidarData(const sensor_msgs::msg::PointCloud2::SharedPtr& cloud) {
    LidarData lidar;
    
    if (!cloud || cloud->width * cloud->height == 0) {
        return lidar;
    }

    sensor_msgs::PointCloud2ConstIterator<float> iter_x(*cloud, "x");
    sensor_msgs::PointCloud2ConstIterator<float> iter_y(*cloud, "y");
    sensor_msgs::PointCloud2ConstIterator<float> iter_z(*cloud, "z");

    lidar.is_dense = true;

    for (; iter_x != iter_x.end(); ++iter_x, ++iter_y, ++iter_z) {
        lidar.points.push_back({*iter_x, *iter_y, *iter_z});
        if (!std::isfinite(*iter_x) || !std::isfinite(*iter_y) || !std::isfinite(*iter_z)) {
            lidar.is_dense = false;
        }
    }

    bool has_intensity = false;
    for (const auto& field : cloud->fields) {
        if (field.name == "intensity") {
            has_intensity = true;
            break;
        }
    }

    if (has_intensity) {
        sensor_msgs::PointCloud2ConstIterator<float> iter_intensity(*cloud, "intensity");
        for (; iter_intensity != iter_intensity.end(); ++iter_intensity) {
            lidar.intensities.push_back(*iter_intensity);
        }
    }

    lidar.timeStamp = cloud->header.stamp.sec + (cloud->header.stamp.nanosec * 1e-9);

    return lidar;
}

class LidarNode : public rclcpp::Node {
public:
    LidarNode(const std::string& topic, const std::string& node_name) : Node(node_name) {
        sub_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
            topic, 10, std::bind(&LidarNode::pointcloud_callback, this, std::placeholders::_1)
        );
    }

    LidarData getLidarData() {
        std::lock_guard<std::mutex> lock(mutex_);
        return pointCloud2LidarData(last_cloud_);
    }

    sensor_msgs::msg::PointCloud2::SharedPtr get_point_cloud() {
        std::lock_guard<std::mutex> lock(mutex_);
        return last_cloud_;
    }

private:
    void pointcloud_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg) {
        std::lock_guard<std::mutex> lock(mutex_);
        last_cloud_ = msg;
    }

    rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_;
    sensor_msgs::msg::PointCloud2::SharedPtr last_cloud_;
    std::mutex mutex_;
};