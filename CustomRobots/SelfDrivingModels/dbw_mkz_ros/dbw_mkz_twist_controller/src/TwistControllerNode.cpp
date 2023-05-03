/*********************************************************************
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2015-2016, Dataspeed Inc.
 *  All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above
 *     copyright notice, this list of conditions and the following
 *     disclaimer in the documentation and/or other materials provided
 *     with the distribution.
 *   * Neither the name of Dataspeed Inc. nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 *  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 *  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 *  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 *  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 *  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 *  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 *  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 *  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 *********************************************************************/

#include "TwistControllerNode.h"

namespace dbw_mkz_twist_controller {

TwistControllerNode::TwistControllerNode(ros::NodeHandle n, ros::NodeHandle pn)
{
  lpf_fuel_.setParams(60.0, 0.1);
  accel_pid_.setRange(0.0, 1.0);

  // Control rate parameter
  double control_rate;
  pn.param("control_rate", control_rate, 50.0);
  control_period_ = 1.0 / control_rate;

  // Ackermann steering parameters
  acker_wheelbase_ = 2.8498;
  acker_track_ = 1.6002;
  steering_ratio_ = 16.0;
  pn.getParam("ackermann_wheelbase", acker_wheelbase_);
  pn.getParam("ackermann_track", acker_track_);
  pn.getParam("steering_ratio", steering_ratio_);
  yaw_control_.setWheelBase(acker_wheelbase_);
  yaw_control_.setSteeringRatio(steering_ratio_);
  yaw_control_.setSpeedMin(mphToMps(4.0));

  // Subscribers
  sub_twist_ = n.subscribe("cmd_vel", 1, &TwistControllerNode::recvTwist, this);
  sub_twist2_ = n.subscribe("cmd_vel_with_limits", 1, &TwistControllerNode::recvTwist2, this);
  sub_twist3_ = n.subscribe("cmd_vel_stamped", 1, &TwistControllerNode::recvTwist3, this);
  sub_steering_ = n.subscribe("steering_report", 1, &TwistControllerNode::recvSteeringReport, this);
  sub_imu_ = n.subscribe("imu/data_raw", 1, &TwistControllerNode::recvImu, this);
  sub_enable_ = n.subscribe("dbw_enabled", 1, &TwistControllerNode::recvEnable, this);
  sub_fuel_level_ = n.subscribe("fuel_level_report", 1, &TwistControllerNode::recvFuel, this);

  // Publishers
  pub_throttle_ = n.advertise<dbw_mkz_msgs::ThrottleCmd>("throttle_cmd", 1);
  pub_brake_ = n.advertise<dbw_mkz_msgs::BrakeCmd>("brake_cmd", 1);
  pub_steering_ = n.advertise<dbw_mkz_msgs::SteeringCmd>("steering_cmd", 1);

  // Debug
  pub_accel_ = n.advertise<std_msgs::Float64>("filtered_accel", 1);
  pub_req_accel_ = n.advertise<std_msgs::Float64>("req_accel", 1);

  // Timers
  control_timer_ = n.createTimer(ros::Duration(control_period_), &TwistControllerNode::controlCallback, this);

  // Dynamic reconfigure
  srv_.setCallback(boost::bind(&TwistControllerNode::reconfig, this, _1, _2));
}

void TwistControllerNode::controlCallback(const ros::TimerEvent& event)
{
  if ((event.current_real - cmd_stamp_).toSec() > (10.0 * control_period_)) {
    speed_pid_.resetIntegrator();
    accel_pid_.resetIntegrator();
    return;
  }

  double vehicle_mass = cfg_.vehicle_mass + lpf_fuel_.get() / 100.0 * cfg_.fuel_capacity * GAS_DENSITY;
  double vel_error = cmd_vel_.twist.linear.x - actual_.linear.x;
  if ((fabs(cmd_vel_.twist.linear.x) < mphToMps(1.0)) || !cfg_.pub_pedals) {
    speed_pid_.resetIntegrator();
  }

  speed_pid_.setRange(
      -std::min(fabs(cmd_vel_.decel_limit) > 0.0 ? fabs(cmd_vel_.decel_limit) : 9.8,
                cfg_.decel_max > 0.0 ? cfg_.decel_max : 9.8),
       std::min(fabs(cmd_vel_.accel_limit) > 0.0 ? fabs(cmd_vel_.accel_limit) : 9.8,
                cfg_.accel_max > 0.0 ? cfg_.accel_max : 9.8)
  );
  double accel_cmd = speed_pid_.step(vel_error, control_period_);

  const double MIN_SPEED = mphToMps(5.0);
  if (cmd_vel_.twist.linear.x <= (double)1e-2) {
    accel_cmd = std::min(accel_cmd, -530 / vehicle_mass / cfg_.wheel_radius);
  } else if (cmd_vel_.twist.linear.x < MIN_SPEED) {
    cmd_vel_.twist.angular.z *= MIN_SPEED / cmd_vel_.twist.linear.x;
    cmd_vel_.twist.linear.x = MIN_SPEED;
  }

  std_msgs::Float64 accel_cmd_msg;
  accel_cmd_msg.data = accel_cmd;
  pub_req_accel_.publish(accel_cmd_msg);

  if (sys_enable_) {
    dbw_mkz_msgs::ThrottleCmd throttle_cmd;
    dbw_mkz_msgs::BrakeCmd brake_cmd;
    dbw_mkz_msgs::SteeringCmd steering_cmd;

    throttle_cmd.enable = true;
    throttle_cmd.pedal_cmd_type = dbw_mkz_msgs::ThrottleCmd::CMD_PERCENT;
    if (accel_cmd >= 0) {
      throttle_cmd.pedal_cmd = accel_pid_.step(accel_cmd - lpf_accel_.get(), control_period_);
    } else {
      accel_pid_.resetIntegrator();
      throttle_cmd.pedal_cmd = 0;
    }

    brake_cmd.enable = true;
    brake_cmd.pedal_cmd_type = dbw_mkz_msgs::BrakeCmd::CMD_TORQUE;
    if ((accel_cmd < -cfg_.brake_deadband) || (cmd_vel_.twist.linear.x < MIN_SPEED)) {
      brake_cmd.pedal_cmd = -accel_cmd * vehicle_mass * cfg_.wheel_radius;
    } else {
      brake_cmd.pedal_cmd = 0;
    }

    steering_cmd.enable = true;
    steering_cmd.steering_wheel_angle_cmd = yaw_control_.getSteeringWheelAngle(cmd_vel_.twist.linear.x, cmd_vel_.twist.angular.z, actual_.linear.x)
        + cfg_.steer_kp * (cmd_vel_.twist.angular.z - actual_.angular.z);

    if (cfg_.pub_pedals) {
      pub_throttle_.publish(throttle_cmd);
      pub_brake_.publish(brake_cmd);
    }

    if (cfg_.pub_steering) {
      pub_steering_.publish(steering_cmd);
    }
  } else {
    speed_pid_.resetIntegrator();
    accel_pid_.resetIntegrator();
  }
}

void TwistControllerNode::reconfig(ControllerConfig& config, uint32_t level)
{
  cfg_ = config;
  cfg_.vehicle_mass -= cfg_.fuel_capacity * GAS_DENSITY; // Subtract weight of full gas tank
  cfg_.vehicle_mass += 150.0; // Account for some passengers

  speed_pid_.setGains(cfg_.speed_kp, 0.0, 0.0);
  accel_pid_.setGains(cfg_.accel_kp, cfg_.accel_ki, 0.0);
  yaw_control_.setLateralAccelMax(cfg_.max_lat_accel);
  lpf_accel_.setParams(cfg_.accel_tau, 0.02);
}

void TwistControllerNode::recvTwist(const geometry_msgs::Twist::ConstPtr& msg)
{
  cmd_vel_.twist = *msg;
  cmd_vel_.accel_limit = 0;
  cmd_vel_.decel_limit = 0;
  cmd_stamp_ = ros::Time::now();
}

void TwistControllerNode::recvTwist2(const dbw_mkz_msgs::TwistCmd::ConstPtr& msg)
{
  cmd_vel_ = *msg;
  cmd_stamp_ = ros::Time::now();
}

void TwistControllerNode::recvTwist3(const geometry_msgs::TwistStamped::ConstPtr& msg)
{
  cmd_vel_.twist = msg->twist;
  cmd_vel_.accel_limit = 0;
  cmd_vel_.decel_limit = 0;
  cmd_stamp_ = ros::Time::now();
}

void TwistControllerNode::recvFuel(const dbw_mkz_msgs::FuelLevelReport::ConstPtr& msg)
{
  lpf_fuel_.filt(msg->fuel_level);
}

void TwistControllerNode::recvSteeringReport(const dbw_mkz_msgs::SteeringReport::ConstPtr& msg)
{
  double raw_accel = 50.0 * (msg->speed - actual_.linear.x);
  lpf_accel_.filt(raw_accel);

  std_msgs::Float64 accel_msg;
  accel_msg.data = lpf_accel_.get();
  pub_accel_.publish(accel_msg);

  actual_.linear.x = msg->speed;
}

void TwistControllerNode::recvImu(const sensor_msgs::Imu::ConstPtr& msg)
{
  actual_.angular.z = msg->angular_velocity.z;
}

void TwistControllerNode::recvEnable(const std_msgs::Bool::ConstPtr& msg)
{
  sys_enable_ = msg->data;
}

}
