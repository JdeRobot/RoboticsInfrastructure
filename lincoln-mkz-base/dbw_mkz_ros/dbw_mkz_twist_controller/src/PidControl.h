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

#ifndef PIDCONTROL_H
#define PIDCONTROL_H

#include <math.h>

namespace dbw_mkz_twist_controller {

class PidControl {
public:
    PidControl() {
      last_error_ = 0.0; int_val_ = 0.0; last_int_val_ = 0.0;
      kp_ = 0.0; ki_ = 0.0; kd_ = 0.0; min_ = -INFINITY; max_ = INFINITY;
    }
    PidControl(double kp, double ki, double kd, double min, double max) {
      last_error_ = 0.0; int_val_ = 0.0; last_int_val_ = 0.0;
      kp_ = kp; ki_ = ki; kd_ = kd; min_ = std::min(min,max); max_ = std::max(min,max);
    }

    void setGains(double kp, double ki, double kd) { kp_ = kp; ki_ = ki; kd_ = kd; }
    void setRange(double min, double max) { min_ = std::min(min,max); max_ = std::max(min,max); }
    void setParams(double kp, double ki, double kd, double min, double max) { setGains(kp,ki,kd); setRange(min,max); }
    void resetIntegrator() { int_val_ = 0.0; last_int_val_ = 0.0; }
    void revertIntegrator() { int_val_ = last_int_val_; }

    double step(double error, double sample_time) {
      last_int_val_ = int_val_;

      double integral = int_val_ + error * sample_time;
      double derivative = (error - last_error_) / sample_time;

      double y = kp_ * error + ki_ * int_val_ + kd_ * derivative;
      if (y > max_) {
        y = max_;
      } else if (y < min_) {
        y = min_;
      } else {
        int_val_ = integral;
      }
      last_error_ = error;
      return y;
    }

private:
    double last_error_;
    double int_val_, last_int_val_;
    double kp_, ki_, kd_;
    double min_, max_;
};

}

#endif // PIDCONTROL_H
