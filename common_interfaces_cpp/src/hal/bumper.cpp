#include "common_interfaces_cpp/hal/bumper.hpp"
#include <sstream>
#include <functional>

BumperData::BumperData() {
    state = 0;
    bumper = CENTER_BUMPER;
}

std::string BumperData::to_string() const {
    std::ostringstream oss;
    oss << "Bumper: {\n   state: " << state
        << "\n   bumper: " << bumper << "\n}";
    return oss.str();
}

BumperData contactsToBumperData(const std::vector<ros_gz_interfaces::msg::Contacts>& contacts) {
    BumperData bumper_data;

    for (size_t i = 0; i < contacts.size(); ++i) {
        if (contacts[i].contacts.size() > 0) {
            bumper_data.state = 1;
            bumper_data.bumper = i;
            break;
        }
    }

    return bumper_data;
}

BumperNode::BumperNode(const std::vector<std::string>& topics_list) 
    : Node("bumper_node"), topics(topics_list), contact_states_(3) {
    
    std::vector<std::function<void(const ros_gz_interfaces::msg::Contacts::SharedPtr)>> callbacks_ = {
        std::bind(&BumperNode::right_callback, this, std::placeholders::_1),
        std::bind(&BumperNode::center_callback, this, std::placeholders::_1),
        std::bind(&BumperNode::left_callback, this, std::placeholders::_1)
    };

    for (size_t i = 0; i < topics.size(); ++i) {
        subs_.push_back(this->create_subscription<ros_gz_interfaces::msg::Contacts>(
            topics[i], 10, callbacks_[i]
        ));
    }
}

void BumperNode::right_callback(const ros_gz_interfaces::msg::Contacts::SharedPtr contact) {
    contact_states_[0] = *contact;
}

void BumperNode::center_callback(const ros_gz_interfaces::msg::Contacts::SharedPtr contact) {
    contact_states_[1] = *contact;
}

void BumperNode::left_callback(const ros_gz_interfaces::msg::Contacts::SharedPtr contact) {
    contact_states_[2] = *contact;
}

BumperData BumperNode::getBumperData() const {
    return contactsToBumperData(contact_states_);
}