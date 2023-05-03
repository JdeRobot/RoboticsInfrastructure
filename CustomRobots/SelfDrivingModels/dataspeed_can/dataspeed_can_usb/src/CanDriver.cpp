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

#include <dataspeed_can_usb/CanDriver.h>
#include <dataspeed_can_usb/CanUsb.h>

namespace dataspeed_can_usb
{

static bool getParamHex(const ros::NodeHandle &nh, const std::string& key, int& i) {
  if (nh.getParam(key, i)) {
    return true;
  } else {
    std::string str;
    if (nh.getParam(key, str)) {
      if (str.length() > 2) {
        if ((str.at(0) == '0') && (str.at(1) == 'x')) {
          unsigned int u;
          std::stringstream ss;
          ss << std::hex << str.substr(2);
          ss >> u;
          if (!ss.fail()) {
            i = u;
            return true;
          }
        }
      }
    }
  }
  return false;
}

CanDriver::CanDriver(ros::NodeHandle &nh, ros::NodeHandle &nh_priv, lusb::UsbDevice *dev, const std::string &name) : nh_(nh), name_(name)
{
  dev_ = new CanUsb(dev);
  dev_->setRecvCallback(boost::bind(&CanDriver::recvDevice, this, _1, _2, _3, _4, _5));

  // Get Parameters
  sync_time_ = false;
#if 0
  priv_nh.getParam("sync_time", sync_time_);
#endif
  int bitrate = 0;
  nh_priv.getParam("bitrate", bitrate);

  bitrates_.resize(CanUsb::MAX_CHANNELS, bitrate);
  filter_masks_.resize(CanUsb::MAX_CHANNELS);
  filter_matches_.resize(CanUsb::MAX_CHANNELS);
  for (unsigned int i = 0; i < CanUsb::MAX_CHANNELS; i++) {
    std::stringstream ss;
    ss << "bitrate_" << (i + 1);
    nh_priv.getParam(ss.str(), bitrates_[i]);
    for (unsigned int j = 0; j < CanUsb::MAX_FILTERS; j++) {
      bool success = true;
      int mask, match;
      std::stringstream ss1, ss2;
      ss1 << "channel_" << (i + 1) << "_mask_" << j;
      ss2 << "channel_" << (i + 1) << "_match_" << j;
      success &= getParamHex(nh_priv, ss1.str(), mask);
      success &= getParamHex(nh_priv, ss2.str(), match);
      if (success) {
        filter_masks_[i].push_back((uint32_t)mask);
        filter_matches_[i].push_back((uint32_t)match);
      }
    }
  }

  serviceDevice();

  // Set up Timers
  timer_service_ = nh.createWallTimer(ros::WallDuration(0.1), &CanDriver::timerServiceCallback, this);
  timer_flush_ = nh.createWallTimer(ros::WallDuration(0.001), &CanDriver::timerFlushCallback, this);
}

CanDriver::~CanDriver()
{
  if (dev_) {
    if (dev_->isOpen()) {
      dev_->reset();
    }
    delete dev_;
    dev_ = NULL;
  }
}

void CanDriver::recvRos(const dataspeed_can_msgs::CanMessage::ConstPtr& msg, unsigned int channel)
{
  dev_->sendMessage(channel, msg->id, msg->extended, msg->dlc, msg->data.elems);
}

void CanDriver::recvDevice(unsigned int channel, uint32_t id, bool extended, uint8_t dlc, const uint8_t data[8])
{
  boost::lock_guard<boost::mutex> lock(mutex_);
  if (channel < pubs_.size()) {
    dataspeed_can_msgs::CanMessageStamped msg;
    msg.header.stamp = ros::Time::now();
    msg.msg.id = id;
    msg.msg.extended = extended;
    msg.msg.dlc = dlc;
    memcpy(msg.msg.data.elems, data, 8);
    pubs_[channel].publish(msg);
  }
}

bool CanDriver::sampleTimeOffset(ros::WallDuration &offset, ros::WallDuration &delay) {
  unsigned int dev_time;
  ros::WallTime t0 = ros::WallTime::now();
  if (dev_->getTimeStamp(dev_time)) {
    ros::WallTime t2 = ros::WallTime::now();
    ros::WallTime t1 = stampDev2Ros(dev_time);
    delay = t2 - t0;
    int64_t nsec = (t2 - t0).toNSec();
    ros::WallDuration delta;
    delta.fromNSec(nsec / 2);
    ros::WallTime asdf = t0 + delta;
    offset = asdf - t1;
    return true;
  }
  return false;
}

void CanDriver::serviceDevice()
{
  if (!dev_->isOpen()) {
    boost::lock_guard<boost::mutex> lock(mutex_);
    pubs_.clear();
    subs_.clear();
    if (dev_->open()) {
      if (dev_->reset()) {
        ROS_INFO("%s: version %s", name_.c_str(), dev_->version().c_str());
        bool synced = false;
        if (sync_time_) {
          ROS_INFO("%s: Synchronizing time...", name_.c_str());
          ros::WallDuration offset, delay;
          for (unsigned int i = 0; i < 10; i++) {
            sampleTimeOffset(offset, delay);
            ROS_INFO("%s: Offset: %f seconds, Delay: %f seconds", name_.c_str(), offset.toSec(), delay.toSec());
          }
          synced = true;
        }
        if (!sync_time_ || synced) {
          bool success = true;
          for (unsigned int i = 0; i < dev_->numChannels(); i++) {
            for (unsigned int j = 0; j < std::min(filter_masks_[i].size(), filter_matches_[i].size()); j++) {
              if (dev_->addFilter(i, filter_masks_[i][j], filter_matches_[i][j])) {
                ROS_INFO("%s: Ch%u, Mask: 0x%08X, Match: 0x%08X", name_.c_str(), i + 1, filter_masks_[i][j], filter_matches_[i][j]);
              } else {
                ROS_WARN("%s: Ch%u, Mask: 0x%08X, Match: 0x%08X failed", name_.c_str(), i + 1, filter_masks_[i][j], filter_matches_[i][j]);
              }
            }
          }
          for (unsigned int i = 0; i < dev_->numChannels(); i++) {
            int bitrate = i < bitrates_.size() ? bitrates_[i] : 0;
            if (dev_->setBitrate(i, bitrate)) {
              ROS_INFO("%s: Ch%u %ukbps", name_.c_str(), i + 1, bitrate / 1000);
            } else {
              ROS_WARN("%s: Ch%u %ukbps failed", name_.c_str(), i + 1, bitrate / 1000);
              success = false;
            }
          }
          if (success) {
            // Set up Publishers and Subscribers
            for (unsigned int i = 0; i < dev_->numChannels(); i++) {
              if (i < bitrates_.size() && bitrates_[i]) {
                std::stringstream ns;
                ns << "can_bus_" << (i + 1);
                ros::NodeHandle node(nh_, ns.str());
                subs_.push_back(node.subscribe<dataspeed_can_msgs::CanMessage>("can_tx", 100, boost::bind(&CanDriver::recvRos, this, _1, i)));
                pubs_.push_back(node.advertise<dataspeed_can_msgs::CanMessageStamped>("can_rx", 100, false));
              } else {
                subs_.push_back(ros::Subscriber());
                pubs_.push_back(ros::Publisher());
              }
            }
#if 0
            unsigned char asdf[] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef};
            for (unsigned int i = 0; i < 0x100 + 1; i++) {
              dev_->sendMessage(0, 0x100 + i, false, 8, asdf);
            }
#endif
          } else {
            dev_->reset();
            dev_->closeDevice();
            ROS_WARN("%s: Failed to set bitrate", name_.c_str());
          }
        } else {
          dev_->closeDevice();
          ROS_WARN("%s: Failed to sync time", name_.c_str());
        }
      } else {
        dev_->closeDevice();
        ROS_WARN("%s: Failed to reset", name_.c_str());
      }
    } else {
      ROS_WARN_THROTTLE(10.0, "%s: not found", name_.c_str());
    }
  } else {
    std::vector<uint32_t> rx_drops, tx_drops;
    if (dev_->getStats(rx_drops, tx_drops, true)) {
      unsigned int size = std::min(rx_drops.size(), tx_drops.size());
      uint32_t total = 0;
      for (unsigned int i = 0; i < size; i++) {
        total += rx_drops[i];
        total += tx_drops[i];
      }
      if (total) {
        std::stringstream ss;
        for (unsigned int i = 0; i < size; i++) {
          ss << "Rx" << (i + 1) << ": " << rx_drops[i] << ", ";
          ss << "Tx" << (i + 1) << ": " << tx_drops[i] << ", ";
        }
        ROS_WARN("Dropped CAN messages: %s", ss.str().c_str());
      }
    }
  }
}

void CanDriver::timerServiceCallback(const ros::WallTimerEvent& event)
{
  serviceDevice();
}

void CanDriver::timerFlushCallback(const ros::WallTimerEvent& event)
{
  dev_->flushMessages();
}

} // namespace dataspeed_can_usb
