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
#include <rosbag/bag.h>
#include <rosbag/view.h>
#include <boost/foreach.hpp>
#include <dataspeed_can_msgs/CanMessageStamped.h>

#include "CanExtractor.h"

int main(int argc, char** argv)
{
  if (argc < 3) {
    printf("Usage: dbc_bag <dbc_file> <bag_file> [ns0] [ns1] [ns3]\n");
    return 0;
  }
  std::string dbc_file = argv[1];
  std::string bag_file_in = argv[2];
  std::string bag_file_out = bag_file_in + ".dbc.bag";
  std::vector<std::string> topics;
  for (unsigned int i = 3; i < argc; i++) {
    topics.push_back(std::string(argv[i]));
  }
  if (topics.empty()) {
    topics.push_back(std::string("/can_bus_dbw/can_rx"));
  }

  printf("Opening dbc file '%s'\n", dbc_file.c_str());
  dataspeed_can_tools::CanExtractor extractor(dbc_file);

  printf("Opening bag file for reading '%s'\n", bag_file_in.c_str());
  rosbag::Bag raw_bag;
  raw_bag.open(bag_file_in, rosbag::bagmode::Read);
  rosbag::View view(raw_bag, rosbag::TopicQuery(topics));

  printf("Opening bag file for writing '%s'\n", bag_file_out.c_str());
  extractor.openBag(bag_file_out);

  double total_time = (view.getEndTime() - view.getBeginTime()).toSec();
  int last_percent = 0;

  BOOST_FOREACH(rosbag::MessageInstance const m, view) {
    dataspeed_can_msgs::CanMessageStamped::ConstPtr msg = m.instantiate<dataspeed_can_msgs::CanMessageStamped>();

    double current_time = (msg->header.stamp - view.getBeginTime()).toSec();
    if ((int)(100 * current_time / total_time) >= last_percent) {
      printf("Processing: %d%% complete\n", last_percent);
      last_percent += 10;
    }

    dataspeed_can_tools::RosCanMsgStruct can_msg;
    can_msg.id = msg->msg.id;
    extractor.getMessage(can_msg);
    extractor.pubMessage(msg);
  }

  extractor.closeBag();
  printf("Successfully wrote parsed CAN data to bag\n");

  return 0;
}
