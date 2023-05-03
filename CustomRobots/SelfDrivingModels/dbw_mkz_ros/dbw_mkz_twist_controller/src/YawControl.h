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

#ifndef YAWCONTROL_H
#define YAWCONTROL_H

#include <math.h>
#include "RadiusControl.h"

namespace dbw_mkz_twist_controller {

class YawControl {
public:
  YawControl() : radius_control_(), speed_min_(1.8), lateral_accel_max_(INFINITY) {}
  YawControl(double wheelbase, double steering_ratio, double speed_min = 1.8, double steering_wheel_angle_max = INFINITY, double lateral_accel_max = INFINITY) :
    radius_control_(wheelbase, steering_ratio, steering_wheel_angle_max), speed_min_(fabs(speed_min)), lateral_accel_max_(fabs(lateral_accel_max)) {}
  void setWheelBase(double val) { radius_control_.setWheelBase(val); }
  void setSteeringRatio(double val) { radius_control_.setSteeringRatio(val); }
  void setSteeringWheelAngleMax(double val) { radius_control_.setSteeringWheelAngleMax(val); }
  void setSpeedMin(double val) { speed_min_ = fabs(val); }
  void setLateralAccelMax(double val) { lateral_accel_max_ = fabs(val); }
  double getSteeringWheelAngle(double cmd_vx, double cmd_wz, double speed) {
    cmd_wz = fabs(cmd_vx) > 0 ? cmd_wz * speed / cmd_vx : 0.0;
    if (fabs(speed) > 0.1) {
      double max_yaw_rate = fabs(lateral_accel_max_ / speed);
      if (cmd_wz > max_yaw_rate) {
        cmd_wz = max_yaw_rate;
      } else if (cmd_wz < -max_yaw_rate) {
        cmd_wz = -max_yaw_rate;
      }
    }
    return radius_control_.getSteeringWheelAngle(std::max(speed, speed_min_) / cmd_wz);
  }
private:
  RadiusControl radius_control_;
  double speed_min_;
  double lateral_accel_max_;
};

}

#endif // YAWCONTROL_H
