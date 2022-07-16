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

#ifndef RADIUSCONTROL_H
#define RADIUSCONTROL_H

#include <math.h>

namespace dbw_mkz_twist_controller {

class RadiusControl {
public:
  RadiusControl() : wheelbase_(1.0), steering_ratio_(1.0), angle_max_(INFINITY) {}
  RadiusControl(double wheelbase, double steering_ratio, double steering_wheel_angle_max = INFINITY) :
    wheelbase_(wheelbase), steering_ratio_(steering_ratio), angle_max_(fabs(steering_wheel_angle_max)) {}
  void setWheelBase(double val) { wheelbase_ = val; }
  void setSteeringRatio(double val) { steering_ratio_ = val; }
  void setSteeringWheelAngleMax(double val) { angle_max_ = fabs(val); }
  double getSteeringWheelAngle(double radius) {
    double angle = isnan(radius) ? 0.0 : atan(wheelbase_ / radius) * steering_ratio_;
    if (angle > angle_max_) {
      return angle_max_;
    } else if (angle < -angle_max_) {
      return -angle_max_;
    }
    return angle;
  }
private:
  double wheelbase_;
  double steering_ratio_;
  double angle_max_;
};

}

#endif // RADIUSCONTROL_H
