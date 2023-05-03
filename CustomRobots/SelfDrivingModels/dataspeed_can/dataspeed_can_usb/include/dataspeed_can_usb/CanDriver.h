/*********************************************************************
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2015-2017, Dataspeed Inc.
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

#ifndef _CAN_DRIVER_H_
#define _CAN_DRIVER_H_

#include <ros/ros.h>

// ROS messages
#include <dataspeed_can_msgs/CanMessageStamped.h>

// Mutex
#include <boost/thread/mutex.hpp>
#include <boost/thread/lock_guard.hpp>

namespace lusb
{
class UsbDevice;
}

namespace dataspeed_can_usb
{
class CanUsb;

class CanDriver
{
public:
  CanDriver(ros::NodeHandle &nh, ros::NodeHandle &nh_priv, lusb::UsbDevice *dev = NULL,
            const std::string &name = std::string("Dataspeed USB CAN Tool"));
  ~CanDriver();

private:
  void timerServiceCallback(const ros::WallTimerEvent& event);
  void timerFlushCallback(const ros::WallTimerEvent& event);
  void recvRos(const dataspeed_can_msgs::CanMessage::ConstPtr& msg, unsigned int channel);

  void recvDevice(unsigned int channel, uint32_t id, bool extended, uint8_t dlc, const uint8_t data[8]);
  void serviceDevice();
  bool sampleTimeOffset(ros::WallDuration &offset, ros::WallDuration &delay);
  inline ros::WallTime stampDev2Ros(unsigned int dev_stamp) {
    return ros::WallTime(dev_stamp / 1000000, (dev_stamp % 1000000) * 1000);
  }

  // NodeHandle
  ros::NodeHandle nh_;

  // Parameters
  bool sync_time_;
  std::vector<int> bitrates_;
  std::vector<std::vector<uint32_t> > filter_masks_;
  std::vector<std::vector<uint32_t> > filter_matches_;

  // Timers
  ros::WallTimer timer_service_;
  ros::WallTimer timer_flush_;

  // USB Device
  CanUsb *dev_;

  // Subscribed topics
  std::vector<ros::Subscriber> subs_;

  // Published topics
  std::vector<ros::Publisher> pubs_;

  // Mutex for vector of publishers
  boost::mutex mutex_;

  // Name prefix for print statements
  std::string name_;
};

} // namespace dataspeed_can_usb

#endif // _CAN_DRIVER_H_
