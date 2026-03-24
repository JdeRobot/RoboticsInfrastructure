#ifndef NOISY_ODOMETRY_PLUGIN_HPP_
#define NOISY_ODOMETRY_PLUGIN_HPP_

#include <gz/sim/System.hpp>
#include <gz/sim/Model.hpp>
#include <gz/transport/Node.hpp>
#include <gz/msgs/twist.pb.h>
#include <gz/math/Pose3.hpp>
#include <gz/math/Rand.hpp>

#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>

#include <mutex>
#include <string>
#include <memory>

namespace custom_plugins
{
  class NoisyOdometryPlugin : 
    public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPostUpdate
  {
  public:
    NoisyOdometryPlugin();
    ~NoisyOdometryPlugin() override = default;

    void Configure(const gz::sim::Entity &_entity,
                   const std::shared_ptr<const sdf::Element> &_sdf,
                   gz::sim::EntityComponentManager &_ecm,
                   gz::sim::EventManager &_eventMgr) override;

    void PostUpdate(const gz::sim::UpdateInfo &_info,
                    const gz::sim::EntityComponentManager &_ecm) override;

  private:
    void OnCmdVel(const gz::msgs::Twist &_msg);

    gz::sim::Model model_;
    gz::transport::Node gz_node_;
    
    std::shared_ptr<rclcpp::Node> ros_node_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr ros_pub_;

    std::string ros_topic_;
    std::string gz_cmd_vel_topic_;
    std::string frame_id_;
    std::string child_frame_id_;

    bool initialized_{false};
    gz::math::Pose3d noisy_pose_internal_; // Nuestra "realidad" ruidosa acumulada
    std::chrono::steady_clock::duration last_update_time_{0};

    double current_v_{0.0};
    double current_w_{0.0};

    std::mutex mutex_;
    double gaussian_noise_coeff_{0.0};
  };
} 

#endif