#ifndef COMMON_INTERFACES_CPP__SIM_TIME_HPP_
#define COMMON_INTERFACES_CPP__SIM_TIME_HPP_

#include <string>
#include "rclcpp/rclcpp.hpp"
#include "rosgraph_msgs/msg/clock.hpp"

/* ### AUXILIARY FUNCTIONS */

class SimTimeData {
public:
    SimTimeData();
    int seconds;
    int nanoseconds;

    std::string to_string() const;
};

/*
 * Translates from ROS Clock to JderobotTypes SimTimeData.
 * @param clock: ROS Clock to translate
 * @type clock: Clock
 * @return a SimTimeData translated from clock
 */
SimTimeData simTime2SimTimeData(const rosgraph_msgs::msg::Clock& clock);


/* ### HAL INTERFACE ### */

class SimTimeNode : public rclcpp::Node {
public:
    SimTimeNode();
    SimTimeData getSimTime() const;

private:
    void listener_callback(const rosgraph_msgs::msg::Clock::SharedPtr msg);

    rclcpp::Subscription<rosgraph_msgs::msg::Clock>::SharedPtr sub;
    rosgraph_msgs::msg::Clock last_sim_time_;
};

#endif