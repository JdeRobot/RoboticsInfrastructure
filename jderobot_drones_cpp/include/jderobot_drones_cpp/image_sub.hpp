#ifndef IMAGE_SUB_HPP
#define IMAGE_SUB_HPP

#include <cv_bridge/cv_bridge.h>
#include <image_transport/image_transport.hpp>
#include <opencv2/opencv.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>

class ImageSubscriberNode : public rclcpp::Node {
public:
  ImageSubscriberNode();
  cv::Mat getFrontalImage();
  cv::Mat getVentralImage();

private:
  void frontalCb(const sensor_msgs::msg::Image::SharedPtr msg);
  void ventralCb(const sensor_msgs::msg::Image::SharedPtr msg);

  sensor_msgs::msg::Image::SharedPtr last_frontal_;
  sensor_msgs::msg::Image::SharedPtr last_ventral_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr frontal_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr ventral_sub_;
};

#endif