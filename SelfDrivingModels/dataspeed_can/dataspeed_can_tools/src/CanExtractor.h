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

#ifndef CANEXTRACTOR_H_
#define CANEXTRACTOR_H_

#include <ros/ros.h>
#include <rosbag/bag.h>
#include <ros/package.h>

#include <std_msgs/Bool.h>
#include <std_msgs/UInt8.h>
#include <std_msgs/UInt16.h>
#include <std_msgs/UInt32.h>
#include <std_msgs/UInt64.h>
#include <std_msgs/Int8.h>
#include <std_msgs/Int16.h>
#include <std_msgs/Int32.h>
#include <std_msgs/Int64.h>
#include <std_msgs/Float64.h>

#include <dataspeed_can_msgs/CanMessageStamped.h>
#include "DbcIterator.hpp"

namespace dataspeed_can_tools
{

typedef struct{
  ros::Publisher sig_pub;
  double factor;
  int length;
  double maximum;
  double minimum;
  std::string sig_name;
  double offset;
  ByteOrder order;
  Sign sign;
  int start_bit;
} RosCanSigStruct;

typedef struct{
  ros::Publisher message_pub;
  std::string msg_name;
  int id;
  std::vector<RosCanSigStruct> sigs;
} RosCanMsgStruct;

class CanExtractor{
public:
  CanExtractor(const std::string &dbc_file);

  bool getMessage(RosCanMsgStruct& can_msg);
  void initPublishers(RosCanMsgStruct& can_msg, ros::NodeHandle& nh);
  void openBag(std::string fname);
  void closeBag();
  void pubMessage(const dataspeed_can_msgs::CanMessageStamped& msg);
  void pubMessage(const dataspeed_can_msgs::CanMessageStamped::ConstPtr& msg) { pubMessage(*msg); }

private:

  static uint64_t unsignedSignalData(uint64_t raw_data, const RosCanSigStruct& sig_props);
  static int64_t signedSignalData(uint64_t raw_data, const RosCanSigStruct& sig_props);
  static int getAppropriateSize(const RosCanSigStruct& sig_props, bool output_signed);
  static void registerCanSignalPublisher(RosCanSigStruct& can_sig, ros::NodeHandle& nh_msg);

  ros::NodeHandle nh_;
  DBCIterator dbc_;
  rosbag::Bag bag_;
  bool bag_open_;

  std::map<int, RosCanMsgStruct> msgs_;
  std::map<int, int> unknown_msgs_;
};

}

#endif /* CANEXTRACTOR_H_ */
