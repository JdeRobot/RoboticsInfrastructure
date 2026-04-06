#ifndef COMMON_INTERFACES_CPP__BUMPER_HPP_
#define COMMON_INTERFACES_CPP__BUMPER_HPP_

#include <vector>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "gazebo_msgs/msg/contacts_state.hpp"

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

BumperData contactsToBumperData(const std::vector<gazebo_msgs::msg::ContactsState>& contacts);

/* ### HAL INTERFACE ### */
class BumperNode : public rclcpp::Node {
public:
    BumperNode(const std::vector<std::string>& topics);
    BumperData getBumperData() const;

private:
    void right_callback(const gazebo_msgs::msg::ContactsState::SharedPtr contact);
    void center_callback(const gazebo_msgs::msg::ContactsState::SharedPtr contact);
    void left_callback(const gazebo_msgs::msg::ContactsState::SharedPtr contact);

    std::vector<std::string> topics;
    std::vector<rclcpp::Subscription<gazebo_msgs::msg::ContactsState>::SharedPtr> subs_;
    std::vector<gazebo_msgs::msg::ContactsState> contact_states_;
};

#endif