#include "jderobot_drones_cpp/image_sub.hpp"

ImageSubscriberNode::ImageSubscriberNode() : rclcpp::Node("image_subscriber_node") {
  auto qos_profile = rclcpp::QoS(rclcpp::KeepLast(10)).best_effort().durability_volatile();

  frontal_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
      "/drone0/sensor_measurements/frontal_camera/image_raw", qos_profile,
      std::bind(&ImageSubscriberNode::frontalCb, this, std::placeholders::_1));

  ventral_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
      "/drone0/sensor_measurements/ventral_camera/image_raw", qos_profile,
      std::bind(&ImageSubscriberNode::ventralCb, this, std::placeholders::_1));
}

void ImageSubscriberNode::frontalCb(const sensor_msgs::msg::Image::SharedPtr msg) {
  last_frontal_ = msg;
}

void ImageSubscriberNode::ventralCb(const sensor_msgs::msg::Image::SharedPtr msg) {
  last_ventral_ = msg;
}

cv::Mat ImageSubscriberNode::getFrontalImage() {
  if (!last_frontal_) {
    return cv::Mat();
  }
  try {
    return cv_bridge::toCvCopy(last_frontal_, "bgr8")->image;
  } catch (cv_bridge::Exception &e) {
    RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
    return cv::Mat();
  }
}

cv::Mat ImageSubscriberNode::getVentralImage() {
  if (!last_ventral_) {
    return cv::Mat();
  }
  try {
    return cv_bridge::toCvCopy(last_ventral_, "bgr8")->image;
  } catch (cv_bridge::Exception &e) {
    RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
    return cv::Mat();
  }
}