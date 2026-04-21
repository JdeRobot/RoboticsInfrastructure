#ifndef COMMON_INTERFACES_CPP__CAMERA_HPP_
#define COMMON_INTERFACES_CPP__CAMERA_HPP_

#include <string>
#include <memory>
#include <mutex>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include <opencv2/opencv.hpp>

const int MAXRANGE = 8;
const int MINRANGE = 0;

class Image {
public:
    Image();
    int height;
    int width;
    double timeStamp;
    std::string format;
    cv::Mat data;

    std::string to_string() const;
};

cv::Mat depthToRGB8(const cv::Mat& gray_img_buff, const std::string& encoding);

std::shared_ptr<Image> imageMsg2Image(const sensor_msgs::msg::Image& img);

class CameraNode : public rclcpp::Node {
public:
    CameraNode(const std::string& topic);
    
    std::shared_ptr<Image> getImage() const;

private:
    void listener_callback(const sensor_msgs::msg::Image::SharedPtr msg);
    
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_;
    sensor_msgs::msg::Image last_img_;
    mutable std::mutex img_mutex_;
};

#endif