#include "common_interfaces_cpp/hal/lidar.hpp"
#include <sstream>
#include <cmath>
#include "sensor_msgs/point_cloud2_iterator.hpp"

const double PI = M_PI;

LidarData::LidarData() {
    timeStamp = 0.0;
    min_range = 0.1;
    max_range = 15.0;
    field_of_view = {2.0 * PI / 3.0, PI / 18.0};
    is_dense = true;
}

std::string LidarData::to_string() const {
    std::ostringstream oss;
    oss << "LiDARData:\n"
        << "  timestamp: " << timeStamp << "\n"
        << "  points: " << points.size() << "\n"
        << "  range: [" << min_range << ", " << max_range << "]\n"
        << "  FOV: (" << field_of_view.first << ", " << field_of_view.second << ")\n"
        << "  is_dense: " << (is_dense ? "True" : "False");
    return oss.str();
}

LidarData pointCloud2LidarData(const sensor_msgs::msg::PointCloud2::SharedPtr cloud) {
    LidarData lidar;
    if (!cloud || cloud->width * cloud->height == 0) {
        return lidar;
    }

    // Read XYZ points
    sensor_msgs::PointCloud2ConstIterator<float> iter_x(*cloud, "x");
    sensor_msgs::PointCloud2ConstIterator<float> iter_y(*cloud, "y");
    sensor_msgs::PointCloud2ConstIterator<float> iter_z(*cloud, "z");

    lidar.points.reserve(cloud->width * cloud->height);
    for (; iter_x != iter_x.end(); ++iter_x, ++iter_y, ++iter_z) {
        lidar.points.push_back({*iter_x, *iter_y, *iter_z});
    }

    // Read intensities if available
    bool has_intensity = false;
    for (const auto& field : cloud->fields) {
        if (field.name == "intensity") {
            has_intensity = true;
            break;
        }
    }

    if (has_intensity) {
        sensor_msgs::PointCloud2ConstIterator<float> iter_intensity(*cloud, "intensity");
        lidar.intensities.reserve(cloud->width * cloud->height);
        for (; iter_intensity != iter_intensity.end(); ++iter_intensity) {
            lidar.intensities.push_back(*iter_intensity);
        }
    }

    // Timestamp (ROS 2 Time -> seconds)
    lidar.timeStamp = cloud->header.stamp.sec + (cloud->header.stamp.nanosec * 1e-9);

    // Validate point cloud
    lidar.is_dense = true;
    for (const auto& point : lidar.points) {
        if (!std::isfinite(point[0]) || !std::isfinite(point[1]) || !std::isfinite(point[2])) {
            lidar.is_dense = false;
            break;
        }
    }

    return lidar;
}

LidarNode::LidarNode(const std::string& topic, const std::string& node_name) 
    : Node(node_name), last_cloud_(nullptr) {
    sub_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
        topic, 10, std::bind(&LidarNode::pointcloud_callback, this, std::placeholders::_1)
    );
}

void LidarNode::pointcloud_callback(const sensor_msgs::msg::PointCloud2::SharedPtr cloud) {
    std::lock_guard<std::mutex> guard(lock_);
    last_cloud_ = cloud;
}

LidarData LidarNode::getLidarData() {
    std::lock_guard<std::mutex> guard(lock_);
    return pointCloud2LidarData(last_cloud_);
}

sensor_msgs::msg::PointCloud2::SharedPtr LidarNode::get_point_cloud() {
    std::lock_guard<std::mutex> guard(lock_);
    return last_cloud_;
}