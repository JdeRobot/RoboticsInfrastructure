#include "common_interfaces_cpp/hal/camera.hpp"
#include <sstream>
#include <cmath>
#include <cv_bridge/cv_bridge.h>

const double PI = M_PI;

/* Represents a camera image with metadata and pixel data. */
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

/*
 * Convert a ROS Image message to a JdeRobot Image object.
 *
 * Args:
 * img: ROS sensor_msgs/Image message.
 *
 * Returns:
 * Image object with BGR data, or None if the message is empty.
 */
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
/* ### HAL INTERFACE ### */

/* ROS2 node that subscribes to a camera topic and stores the latest image. */
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

/*
* Return the latest camera image.
*
* Returns:
* Image object with BGR data, or None if no image has been received.
*/
std::shared_ptr<Image> CameraNode::getImage() const {
    /* Store the latest image message received from the topic. */
    sensor_msgs::msg::Image img_copy;
    {
        std::lock_guard<std::mutex> lock(img_mutex_);
        img_copy = last_img_;
    }
    return imageMsg2Image(img_copy);
}