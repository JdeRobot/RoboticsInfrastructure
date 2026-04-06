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

BumperData contactsToBumperData(const std::vector<gazebo_msgs::msg::ContactsState>& contacts) {
    BumperData bumper_data;

    for (size_t i = 0; i < contacts.size(); ++i) {
        if (contacts[i].states.size() > 0) {
            bumper_data.state = 1;
            bumper_data.bumper = i;
            break;
        }
    }

    return bumper_data;
}

BumperNode::BumperNode(const std::vector<std::string>& topics_list) 
    : Node("bumper_node"), topics(topics_list), contact_states_(3) {
    
    // Hardcoded for the moment to three topics
    // as dynamic callback creation is not trivial
    std::vector<std::function<void(const gazebo_msgs::msg::ContactsState::SharedPtr)>> callbacks_ = {
        std::bind(&BumperNode::right_callback, this, std::placeholders::_1),
        std::bind(&BumperNode::center_callback, this, std::placeholders::_1),
        std::bind(&BumperNode::left_callback, this, std::placeholders::_1)
    };

    // Subscribe to all the callbacks
    for (size_t i = 0; i < topics.size(); ++i) {
        subs_.push_back(this->create_subscription<gazebo_msgs::msg::ContactsState>(
            topics[i], 10, callbacks_[i]
        ));
    }

    // Right, center, left
}

void BumperNode::right_callback(const gazebo_msgs::msg::ContactsState::SharedPtr contact) {
    contact_states_[0] = *contact;
}

void BumperNode::center_callback(const gazebo_msgs::msg::ContactsState::SharedPtr contact) {
    contact_states_[1] = *contact;
}

void BumperNode::left_callback(const gazebo_msgs::msg::ContactsState::SharedPtr contact) {
    contact_states_[2] = *contact;
}

BumperData BumperNode::getBumperData() const {
    return contactsToBumperData(contact_states_);
}