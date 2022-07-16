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

#ifndef TWISTCONTROLLERNODE_H_
#define TWISTCONTROLLERNODE_H_

#include <ros/ros.h>
#include <std_msgs/Bool.h>
#include <sensor_msgs/Imu.h>
#include <dbw_mkz_msgs/ThrottleCmd.h>
#include <dbw_mkz_msgs/ThrottleReport.h>
#include <dbw_mkz_msgs/BrakeCmd.h>
#include <dbw_mkz_msgs/BrakeReport.h>
#include <dbw_mkz_msgs/SteeringCmd.h>
#include <dbw_mkz_msgs/SteeringReport.h>
#include <dbw_mkz_msgs/FuelLevelReport.h>
#include <dbw_mkz_msgs/TwistCmd.h>
#include <geometry_msgs/TwistStamped.h>

#include <dynamic_reconfigure/server.h>
#include <dbw_mkz_twist_controller/ControllerConfig.h>

#include "YawControl.h"
#include "PidControl.h"
#include "LowPass.h"

#include <std_msgs/Float64.h>

namespace dbw_mkz_twist_controller {

class TwistControllerNode{
public:
  TwistControllerNode(ros::NodeHandle n, ros::NodeHandle pn);
private:
  void reconfig(ControllerConfig& config, uint32_t level);
  void controlCallback(const ros::TimerEvent& event);
  void recvTwist(const geometry_msgs::Twist::ConstPtr& msg);
  void recvTwist2(const dbw_mkz_msgs::TwistCmd::ConstPtr& msg);
  void recvTwist3(const geometry_msgs::TwistStamped::ConstPtr& msg);
  void recvSteeringReport(const dbw_mkz_msgs::SteeringReport::ConstPtr& msg);
  void recvImu(const sensor_msgs::Imu::ConstPtr& msg);
  void recvEnable(const std_msgs::Bool::ConstPtr& msg);
  void recvFuel(const dbw_mkz_msgs::FuelLevelReport::ConstPtr& msg);

  ros::Publisher pub_throttle_;
  ros::Publisher pub_brake_;
  ros::Publisher pub_steering_;
  ros::Publisher pub_accel_;
  ros::Publisher pub_req_accel_;
  ros::Subscriber sub_steering_;
  ros::Subscriber sub_imu_;
  ros::Subscriber sub_enable_;
  ros::Subscriber sub_twist_;
  ros::Subscriber sub_twist2_;
  ros::Subscriber sub_twist3_;
  ros::Subscriber sub_fuel_level_;
  ros::Timer control_timer_;

  dbw_mkz_msgs::TwistCmd cmd_vel_;
  geometry_msgs::Twist actual_;
  ros::Time cmd_stamp_;
  dynamic_reconfigure::Server<ControllerConfig> srv_;

  PidControl speed_pid_;
  PidControl accel_pid_;
  YawControl yaw_control_;
  LowPass lpf_accel_;
  LowPass lpf_fuel_;
  ControllerConfig cfg_;
  bool sys_enable_;

  // Parameters
  double control_period_;
  double acker_wheelbase_;
  double acker_track_;
  double steering_ratio_;

  static const double GAS_DENSITY = 2.858; // kg/gal
  static double mphToMps(double mph) { return mph * 0.44704; }
};

}

#endif /* TWISTCONTROLLERNODE_H_ */
