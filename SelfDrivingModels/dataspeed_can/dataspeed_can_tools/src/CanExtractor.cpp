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

#include "CanExtractor.h"

namespace dataspeed_can_tools{

CanExtractor::CanExtractor(const std::string &dbc_file) :
    dbc_(dbc_file)
{
  bag_open_ = false;
}

uint64_t CanExtractor::unsignedSignalData(uint64_t raw_data, const RosCanSigStruct& sig_props)
{
  uint64_t mask = (1 << sig_props.length) - 1;

  if (sig_props.order == INTEL) {
    return (raw_data >> sig_props.start_bit) & mask;
  } else {
    int intel_start_bit = 56 - 8 * (sig_props.start_bit / 8) + (sig_props.start_bit % 8) - (sig_props.length - 1);
    return (__builtin_bswap64(raw_data) >> intel_start_bit) & mask;
  }
}

int64_t CanExtractor::signedSignalData(uint64_t raw_data, const RosCanSigStruct& sig_props)
{
  uint64_t mask = (1 << sig_props.length) - 1;
  int64_t val = unsignedSignalData(raw_data, sig_props);

  if (val & (1 << (sig_props.length - 1))) {
    val |= ~mask;
  }

  return val;
}

int CanExtractor::getAppropriateSize(const RosCanSigStruct& sig_props, bool output_signed)
{
  int64_t max_val;
  int64_t min_val;
  if ((sig_props.sign == SIGNED)){
    max_val = (((int64_t)1 << (sig_props.length - 1)) - 1);
    min_val = -((int64_t)1 << (sig_props.length - 1));
  }else{
    max_val = (((int64_t)1 << sig_props.length) - 1);
    min_val = 0;
  }
  max_val = max_val * (int64_t)sig_props.factor + (int64_t)sig_props.offset;
  min_val = min_val * (int64_t)sig_props.factor + (int64_t)sig_props.offset;

  if (output_signed){
    if ((INT8_MIN <= min_val) && (max_val <= INT8_MAX)){
      return 8;
    }else if ((INT16_MIN <= min_val) && (max_val <= INT16_MAX)){
      return 16;
    }else if ((INT32_MIN <= min_val) && (max_val <= INT32_MAX)){
      return 32;
    }else{
      return 64;
    }
  }else{
    if (max_val < UINT8_MAX){
      return 8;
    }else if (max_val < UINT16_MAX){
      return 16;
    }else if (max_val < UINT32_MAX){
      return 32;
    }else{
      return 64;
    }
  }
}

bool CanExtractor::getMessage(RosCanMsgStruct& can_msg)
{
  if (msgs_.find(can_msg.id) == msgs_.end()) {
    for (DBCIterator::const_iterator it = dbc_.begin(); it < dbc_.end(); it++) {
      if (it->getId() == can_msg.id) {
        can_msg.msg_name = it->getName();

        for (Message::const_iterator m_it = it->begin(); m_it < it->end(); m_it++) {
          RosCanSigStruct new_sig;
          new_sig.factor = m_it->getFactor();
          new_sig.length = m_it->getLength();
          new_sig.maximum = m_it->getMaximum();
          new_sig.minimum = m_it->getMinimum();
          new_sig.offset = m_it->getOffset();
          new_sig.order = m_it->getByteOrder();
          new_sig.sig_name = m_it->getName();
          new_sig.sign = m_it->getSign();
          new_sig.start_bit = m_it->getStartbit();
          can_msg.sigs.push_back(new_sig);
        }

        msgs_[can_msg.id] = can_msg;
        return true;
      }
    }

    if (unknown_msgs_.find(can_msg.id) == unknown_msgs_.end()) {
      ROS_WARN("Received unknown CAN message with ID = 0x%X", can_msg.id);
      unknown_msgs_[can_msg.id] = 0;
    }
  } else {
    can_msg = msgs_[can_msg.id];
  }

  return false;
}

void CanExtractor::initPublishers(RosCanMsgStruct& can_msg, ros::NodeHandle& nh)
{
  ros::NodeHandle nh_msg(nh, can_msg.msg_name);

  can_msg.message_pub = nh.advertise<dataspeed_can_msgs::CanMessageStamped>(can_msg.msg_name, 1);

  for (size_t i=0; i<can_msg.sigs.size(); i++){
    registerCanSignalPublisher(can_msg.sigs[i], nh_msg);
  }

  msgs_[can_msg.id] = can_msg;
}

void CanExtractor::openBag(std::string fname)
{
  bag_.open(fname, rosbag::bagmode::Write);
  bag_open_ = true;
}

void CanExtractor::closeBag()
{
  bag_.close();
  bag_open_ = false;
}

void CanExtractor::registerCanSignalPublisher(RosCanSigStruct& can_sig, ros::NodeHandle& nh_msg)
{
  if (can_sig.length == 1) {
    can_sig.sig_pub = nh_msg.advertise<std_msgs::Bool>(can_sig.sig_name, 1);
  } else if ((fmod(can_sig.factor, 1.0) != 0) || (fmod(can_sig.offset, 1.0) != 0)) {
    can_sig.sig_pub = nh_msg.advertise<std_msgs::Float64>(can_sig.sig_name, 1);
  } else {
    if ((can_sig.sign == SIGNED) || (can_sig.offset < 0) || (can_sig.factor < 0)) {
      switch (getAppropriateSize(can_sig, true)) {
        case 8:
          can_sig.sig_pub = nh_msg.advertise<std_msgs::Int8>(can_sig.sig_name, 1);
          break;
        case 16:
          can_sig.sig_pub = nh_msg.advertise<std_msgs::Int16>(can_sig.sig_name, 1);
          break;
        case 32:
          can_sig.sig_pub = nh_msg.advertise<std_msgs::Int32>(can_sig.sig_name, 1);
          break;
        case 64:
          can_sig.sig_pub = nh_msg.advertise<std_msgs::Int64>(can_sig.sig_name, 1);
          break;
      }
    } else {
      switch (getAppropriateSize(can_sig, false)) {
        case 8:
          can_sig.sig_pub = nh_msg.advertise<std_msgs::UInt8>(can_sig.sig_name, 1);
          break;
        case 16:
          can_sig.sig_pub = nh_msg.advertise<std_msgs::UInt16>(can_sig.sig_name, 1);
          break;
        case 32:
          can_sig.sig_pub = nh_msg.advertise<std_msgs::UInt32>(can_sig.sig_name, 1);
          break;
        case 64:
          can_sig.sig_pub = nh_msg.advertise<std_msgs::UInt64>(can_sig.sig_name, 1);
          break;
      }
    }
  }
}

void CanExtractor::pubMessage(const dataspeed_can_msgs::CanMessageStamped& msg)
{
  if (msgs_.find(msg.msg.id) == msgs_.end()){
    return;
  }

  RosCanMsgStruct active_msg = msgs_[msg.msg.id];

  if (bag_open_){
    bag_.write(active_msg.msg_name, msg.header.stamp, msg);
  }else{
    active_msg.message_pub.publish(msg);
  }

  uint64_t raw_data = *((uint64_t*)&msg.msg.data[0]);

  for (size_t i = 0; i < active_msg.sigs.size(); i++) {

    if (active_msg.sigs[i].length == 1) {
      std_msgs::Bool sig_msg;
      if (unsignedSignalData(raw_data, active_msg.sigs[i])) {
        sig_msg.data = true;
      } else {
        sig_msg.data = false;
      }

      if (bag_open_){
        bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
      }else{
        active_msg.sigs[i].sig_pub.publish(sig_msg);
      }
    } else if ((fmod(active_msg.sigs[i].factor, 1.0) != 0) || fmod(active_msg.sigs[i].offset, 1.0) != 0) {
      std_msgs::Float64 sig_msg;
      if (active_msg.sigs[i].sign == SIGNED) {
        sig_msg.data = active_msg.sigs[i].factor * signedSignalData(raw_data, active_msg.sigs[i])
            + active_msg.sigs[i].offset;
      } else {
        sig_msg.data = active_msg.sigs[i].factor * unsignedSignalData(raw_data, active_msg.sigs[i])
            + active_msg.sigs[i].offset;
      }

      if (bag_open_){
        bag_.write(active_msg.msg_name + "/" +active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
      }else{
        active_msg.sigs[i].sig_pub.publish(sig_msg);
      }
    } else {
      if ((active_msg.sigs[i].sign == SIGNED) || (active_msg.sigs[i].offset < 0) || (active_msg.sigs[i].factor < 0)) {
        if (active_msg.sigs[i].sign == SIGNED) {
          switch (getAppropriateSize(active_msg.sigs[i], true)) {
            case 8:
            {
              std_msgs::Int8 sig_msg;
              sig_msg.data = (int8_t)(active_msg.sigs[i].factor * signedSignalData(raw_data, active_msg.sigs[i])
                  + active_msg.sigs[i].offset);

              if (bag_open_){
                bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
              }else{
                active_msg.sigs[i].sig_pub.publish(sig_msg);
              }
            }
              break;
            case 16:
            {
              std_msgs::Int16 sig_msg;
              sig_msg.data = (int16_t)(active_msg.sigs[i].factor * signedSignalData(raw_data, active_msg.sigs[i])
                  + active_msg.sigs[i].offset);

              if (bag_open_){
                bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
              }else{
                active_msg.sigs[i].sig_pub.publish(sig_msg);
              }
            }
              break;
            case 32:
            {
              std_msgs::Int32 sig_msg;
              sig_msg.data = (int32_t)(active_msg.sigs[i].factor * signedSignalData(raw_data, active_msg.sigs[i])
                  + active_msg.sigs[i].offset);

              if (bag_open_){
                bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
              }else{
                active_msg.sigs[i].sig_pub.publish(sig_msg);
              }
            }
              break;
            case 64:
            {
              std_msgs::Int64 sig_msg;
              sig_msg.data = (int64_t)(active_msg.sigs[i].factor * signedSignalData(raw_data, active_msg.sigs[i])
                  + active_msg.sigs[i].offset);

              if (bag_open_){
                bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
              }else{
                active_msg.sigs[i].sig_pub.publish(sig_msg);
              }
            }
              break;
          }
        } else {
          switch (getAppropriateSize(active_msg.sigs[i], true)) {
            case 8:
            {
              std_msgs::Int8 sig_msg;
              sig_msg.data = (int8_t)(active_msg.sigs[i].factor * unsignedSignalData(raw_data, active_msg.sigs[i])
                  + active_msg.sigs[i].offset);

              if (bag_open_){
                bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
              }else{
                active_msg.sigs[i].sig_pub.publish(sig_msg);
              }
            }
              break;
            case 16:
            {
              std_msgs::Int16 sig_msg;
              sig_msg.data = (int16_t)(active_msg.sigs[i].factor
                  * unsignedSignalData(raw_data, active_msg.sigs[i]) + active_msg.sigs[i].offset);
              if (bag_open_){
                bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
              }else{
                active_msg.sigs[i].sig_pub.publish(sig_msg);
              }
            }
              break;
            case 32:
            {
              std_msgs::Int32 sig_msg;
              sig_msg.data = (int32_t)(active_msg.sigs[i].factor
                  * unsignedSignalData(raw_data, active_msg.sigs[i]) + active_msg.sigs[i].offset);
              if (bag_open_){
                bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
              }else{
                active_msg.sigs[i].sig_pub.publish(sig_msg);
              }
            }
              break;
            case 64:
            {
              std_msgs::Int64 sig_msg;
              sig_msg.data = (int64_t)(active_msg.sigs[i].factor
                  * unsignedSignalData(raw_data, active_msg.sigs[i]) + active_msg.sigs[i].offset);
              if (bag_open_){
                bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
              }else{
                active_msg.sigs[i].sig_pub.publish(sig_msg);
              }
            }
              break;
          }
        }
      } else {
        switch (getAppropriateSize(active_msg.sigs[i], false)) {
          case 8:
          {
            std_msgs::UInt8 sig_msg;
            sig_msg.data = (uint8_t)(active_msg.sigs[i].factor * unsignedSignalData(raw_data, active_msg.sigs[i])
                + active_msg.sigs[i].offset);

            if (bag_open_){
              bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
            }else{
              active_msg.sigs[i].sig_pub.publish(sig_msg);
            }
          }
            break;
          case 16:
          {
            std_msgs::UInt16 sig_msg;
            sig_msg.data = (uint16_t)(active_msg.sigs[i].factor * unsignedSignalData(raw_data, active_msg.sigs[i])
                + active_msg.sigs[i].offset);

            if (bag_open_){
              bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
            }else{
              active_msg.sigs[i].sig_pub.publish(sig_msg);
            }
          }
            break;
          case 32:
          {
            std_msgs::UInt32 sig_msg;
            sig_msg.data = (uint32_t)(active_msg.sigs[i].factor * unsignedSignalData(raw_data, active_msg.sigs[i])
                + active_msg.sigs[i].offset);

            if (bag_open_){
              bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
            }else{
              active_msg.sigs[i].sig_pub.publish(sig_msg);
            }
          }
            break;
          case 64:
          {
            std_msgs::UInt64 sig_msg;
            sig_msg.data = (uint64_t)(active_msg.sigs[i].factor * unsignedSignalData(raw_data, active_msg.sigs[i])
                + active_msg.sigs[i].offset);

            if (bag_open_){
              bag_.write(active_msg.msg_name + "/" + active_msg.sigs[i].sig_name, msg.header.stamp, sig_msg);
            }else{
              active_msg.sigs[i].sig_pub.publish(sig_msg);
            }
          }
            break;
        }
      }
    }
  }
}

}
