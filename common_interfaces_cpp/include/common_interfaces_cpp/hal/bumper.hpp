#ifndef COMMON_INTERFACES_CPP__BUMPER_HPP_
#define COMMON_INTERFACES_CPP__BUMPER_HPP_

#include <vector>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "ros_gz_interfaces/msg/contacts.hpp"

/* ### AUXILIARY FUNCTIONS ### */

const int RIGHT_BUMPER = 0;
const int CENTER_BUMPER = 1;
const int LEFT_BUMPER = 2;

class BumperData {
public:
    BumperData();
    int state;
    int bumper;

    std::string to_string() const;
};

BumperData contactsToBumperData(const std::vector<ros_gz_interfaces::msg::Contacts>& contacts);

/* ### HAL INTERFACE ### */
class BumperNode : public rclcpp::Node {
public:
    BumperNode(const std::vector<std::string>& topics);
    BumperData getBumperData() const;

private:
    void right_callback(const ros_gz_interfaces::msg::Contacts::SharedPtr contact);
    void center_callback(const ros_gz_interfaces::msg::Contacts::SharedPtr contact);
    void left_callback(const ros_gz_interfaces::msg::Contacts::SharedPtr contact);

    std::vector<std::string> topics;
    std::vector<rclcpp::Subscription<ros_gz_interfaces::msg::Contacts>::SharedPtr> subs_;
    std::vector<ros_gz_interfaces::msg::Contacts> contact_states_;
};

#endif