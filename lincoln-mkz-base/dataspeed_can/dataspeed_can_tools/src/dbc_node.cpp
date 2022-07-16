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

#include <ros/ros.h>
#include <ros/package.h>
#include "CanExtractor.h"
#include <dataspeed_can_msgs/CanMessageStamped.h>

ros::NodeHandle *nh_;
dataspeed_can_tools::CanExtractor* extractor_;

void recvCanMessage(const dataspeed_can_msgs::CanMessageStamped::ConstPtr& msg)
{
  dataspeed_can_tools::RosCanMsgStruct info;
  info.id = msg->msg.id;

  if (extractor_->getMessage(info)) {
    extractor_->initPublishers(info, *nh_);
  }

  extractor_->pubMessage(msg);
}

int main(int argc, char** argv)
{
  ros::init(argc, argv, "can_parser_node");
  ros::NodeHandle nh; nh_ = &nh;
  ros::NodeHandle nh_priv("~");

  std::string dbc_file;
  if (!nh_priv.getParam("dbc_file", dbc_file)) {
    ROS_FATAL("DBC file not specified. Exiting.");
  }

  ROS_INFO("Opening dbc file: %s", dbc_file.c_str());
  dataspeed_can_tools::CanExtractor extractor(dbc_file);
  extractor_ = &extractor;

  ros::Subscriber sub_can = nh.subscribe("can_rx", 100, recvCanMessage);

  ros::spin();
}
