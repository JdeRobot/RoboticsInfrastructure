#ifndef COMMON_INTERFACES_CPP__SIM_TIME_HPP_
#define COMMON_INTERFACES_CPP__SIM_TIME_HPP_

#include <string>
#include <mutex>
#include "rclcpp/rclcpp.hpp"
#include "rosgraph_msgs/msg/clock.hpp"

/* ### AUXILIARY FUNCTIONS */

class SimTimeData {
public:
    SimTimeData();
    int seconds;
    int nanoseconds;

    std::string to_string() const;
    
    double to_double() const; 
};

SimTimeData simTime2SimTimeData(const rosgraph_msgs::msg::Clock& clock);

/* ### HAL INTERFACE ### */

class SimTimeNode : public rclcpp::Node {
public:
    SimTimeNode(const std::string& node_name = "simulation_time_node");
    SimTimeData getSimTime();

private:
    void listener_callback(const rosgraph_msgs::msg::Clock::SharedPtr msg);

    rclcpp::Subscription<rosgraph_msgs::msg::Clock>::SharedPtr sub;
    rosgraph_msgs::msg::Clock last_sim_time_;
    std::mutex lock_;
};

#endif