#ifndef NOISY_ODOMETRY_PLUGIN_HPP_
#define NOISY_ODOMETRY_PLUGIN_HPP_

#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/twist.pb.h>
#include <gz/math/Pose3.hh>
#include <gz/math/Rand.hh>

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

    // Keeps angles bounded in [-pi, pi] so yaw differences remain well behaved.
    double NormalizeAngle(double _angle) const;

    gz::sim::Model model_;
    gz::transport::Node gz_node_;

    std::shared_ptr<rclcpp::Node> ros_node_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr ros_pub_;

    std::string ros_topic_;
    std::string gz_cmd_vel_topic_;
    std::string frame_id_;
    std::string child_frame_id_;

    bool initialized_{false};

    // Internal odometric estimate that is propagated only with noisy increments.
    // This is the state published as odom_noisy and it is allowed to drift.
    gz::math::Pose3d noisy_pose_internal_;

    // True simulator pose used only to extract the real motion increment
    // between consecutive simulation steps.
    gz::math::Pose3d last_true_pose_;

    std::chrono::steady_clock::duration last_update_time_{0};

    // Latest commanded velocities received from cmd_vel.
    double current_v_{0.0};
    double current_w_{0.0};

    // Last noisy body-frame velocities published in the odometry message.
    double last_noisy_linear_velocity_{0.0};
    double last_noisy_angular_velocity_{0.0};

    std::mutex mutex_;

    // Legacy generic noise parameter kept for compatibility with the original SDF.
    double gaussian_noise_coeff_{0.0};

    // Standard odometry motion-model coefficients.
    // They control how rotation and translation uncertainties affect each other.
    double alpha1_{0.0};
    double alpha2_{0.0};
    double alpha3_{0.0};
    double alpha4_{0.0};

    // Fraction of cmd_vel that leaks into the odometry when the robot is
    // physically blocked (wall contact). Models wheel slip against the obstacle.
    // Typical range: 0.01 – 0.05.
    double slip_factor_{0.02};
  };
}

#endif