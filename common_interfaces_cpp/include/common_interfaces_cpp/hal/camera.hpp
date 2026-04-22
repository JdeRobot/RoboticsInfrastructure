#ifndef COMMON_INTERFACES_CPP__CAMERA_HPP_
#define COMMON_INTERFACES_CPP__CAMERA_HPP_

#include <string>
#include <memory>
#include <mutex>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include <opencv2/opencv.hpp>

/* ### AUXILIARY FUNCTIONS ### */

const int MAXRANGE = 8; // max length received from imageD
const int MINRANGE = 0;

/* Represents a camera image with metadata and pixel data. */
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


/*
 * Convert a ROS Image message to a JdeRobot Image object.
 *
 * Args:
 * img: ROS sensor_msgs/Image message.
 *
 * Returns:
 * Image object with BGR data, or None if the message is empty.
 */
std::shared_ptr<Image> imageMsg2Image(const sensor_msgs::msg::Image& img);

/* ### HAL INTERFACE ### */

/* ROS2 node that subscribes to a camera topic and stores the latest image. */

class CameraNode : public rclcpp::Node {
public:
    CameraNode(const std::string& topic);
    /*
     * Return the latest camera image.
     *
     * Returns:
     * Image object with BGR data, or None if no image has been received.
     */
    std::shared_ptr<Image> getImage() const;

private:
    /* Store the latest image message received from the topic. */
    void listener_callback(const sensor_msgs::msg::Image::SharedPtr msg);
    
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_;
    sensor_msgs::msg::Image last_img_;
    mutable std::mutex img_mutex_;
};

#endif