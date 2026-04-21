#include "common_interfaces_cpp/hal/camera.hpp"
#include <sstream>
#include <cmath>
#include <cv_bridge/cv_bridge.h>

const double PI = M_PI;

Image::Image() {
    height = 480;
    width = 640;
    timeStamp = 0;
    format = "";
    data = cv::Mat::zeros(height, width, CV_8UC3);
}

std::string Image::to_string() const {
    std::ostringstream oss;
    oss << "Image: {\n   height: " << height
        << "\n   width: " << width
        << "\n   format: " << format 
        << "\n   timeStamp: " << timeStamp
        << "\n   data: " << data << "\n}";
    return oss.str();
}

std::shared_ptr<Image> imageMsg2Image(const sensor_msgs::msg::Image& img) {
    if (img.data.empty()) {
        return nullptr;
    }

    auto image = std::make_shared<Image>();

    image->width = img.width;
    image->height = img.height;
    image->format = "BGR8";
    image->timeStamp = img.header.stamp.sec + (img.header.stamp.nanosec * 1e-9);

    cv::Mat cv_image;
    if (img.encoding.length() >= 2 && img.encoding.substr(img.encoding.length() - 2) == "C1") {
        cv::Mat gray_img_buff = cv_bridge::toCvCopy(img, img.encoding)->image;
        cv_image = depthToRGB8(gray_img_buff, img.encoding);
    } else {
        cv_image = cv_bridge::toCvCopy(img, "bgr8")->image;
    }

    image->data = cv_image;
    return image;
}

cv::Mat depthToRGB8(const cv::Mat& gray_img_buff, const std::string& encoding) {
    cv::Mat color_img;
    if (!gray_img_buff.empty()) {
        cv::cvtColor(gray_img_buff, color_img, cv::COLOR_GRAY2BGR);
    }
    return color_img;
}

CameraNode::CameraNode(const std::string& topic) 
    : Node("camera_node") {
    sub_ = this->create_subscription<sensor_msgs::msg::Image>(
        topic, 10, std::bind(&CameraNode::listener_callback, this, std::placeholders::_1)
    );
}

void CameraNode::listener_callback(const sensor_msgs::msg::Image::SharedPtr msg) {
    std::lock_guard<std::mutex> lock(img_mutex_);
    last_img_ = *msg;
}

std::shared_ptr<Image> CameraNode::getImage() const {
    sensor_msgs::msg::Image img_copy;
    {
        std::lock_guard<std::mutex> lock(img_mutex_);
        img_copy = last_img_;
    }
    return imageMsg2Image(img_copy);
}