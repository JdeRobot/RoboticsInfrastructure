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

// ROS and messages
#include <ros/ros.h>
#include <geometry_msgs/Twist.h>
#include <dbw_mkz_msgs/TwistCmd.h>

// Dynamic Reconfigure
#include <dynamic_reconfigure/server.h>
#include <dbw_mkz_twist_controller/TwistTestConfig.h>

// Global variables
dbw_mkz_twist_controller::TwistTestConfig cfg_;
ros::Publisher pub_twist, pub_twist2;

// Static functions
static double mphToMps(double mph) { return mph * 0.44704; }
static double kphToMps(double mph) { return mph * 0.277778; }
static double yawRateFromRadius(double speed, double radius) {
  return radius != 0.0 ? speed / radius : 0.0;
}

// Dynamic Reconfigure callback
void reconfig(dbw_mkz_twist_controller::TwistTestConfig& config, uint32_t level)
{
  cfg_ = config;
}

void timerCallback(const ros::TimerEvent& event)
{
  if (cfg_.publish) {
    dbw_mkz_msgs::TwistCmd cmd;
    switch (cfg_.speed_units) {
      default:
      case dbw_mkz_twist_controller::TwistTest_SPEED_MPS:
        cmd.twist.linear.x = cfg_.speed;
        break;
      case dbw_mkz_twist_controller::TwistTest_SPEED_MPH:
        cmd.twist.linear.x = mphToMps(cfg_.speed);
        break;
      case dbw_mkz_twist_controller::TwistTest_SPEED_KPH:
        cmd.twist.linear.x = kphToMps(cfg_.speed);
        break;
    }
    switch (cfg_.yaw_method) {
      default:
      case dbw_mkz_twist_controller::TwistTest_YAW_RATE:
        cmd.twist.angular.z = cfg_.yaw_rate;
        break;
      case dbw_mkz_twist_controller::TwistTest_YAW_RADIUS:
        cmd.twist.angular.z = yawRateFromRadius(cmd.twist.linear.x, cfg_.yaw_radius);
        break;
    }
    if (cfg_.use_limits) {
      cmd.accel_limit = cfg_.accel_max;
      cmd.decel_limit = cfg_.decel_max;
      pub_twist2.publish(cmd);
    } else {
      pub_twist.publish(cmd.twist);
    }
  }
}

int main(int argc, char** argv)
{
  ros::init(argc, argv, "twist_tester");
  ros::NodeHandle n;

  // Dynamic Reconfigure
  dynamic_reconfigure::Server<dbw_mkz_twist_controller::TwistTestConfig> srv;
  srv.setCallback(boost::bind(reconfig, _1, _2));

  // Publishers
  pub_twist = n.advertise<geometry_msgs::Twist>("cmd_vel", 1);
  pub_twist2 = n.advertise<dbw_mkz_msgs::TwistCmd>("cmd_vel_with_limits", 1);

  // Timer
  ros::Timer timer = n.createTimer(ros::Duration(1/20.0), timerCallback);

  // Handle callbacks
  ros::spin();

  return 0;
}
