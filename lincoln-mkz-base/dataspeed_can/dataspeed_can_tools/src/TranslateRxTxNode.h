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

#ifndef _TRANSLATE_RX_TX_H_
#define _TRANSLATE_RX_TX_H_

#include <ros/ros.h>
#include <dataspeed_can_msgs/CanMessageStamped.h>

namespace dataspeed_can_tools
{

class TranslateRxTxNode
{
public:
  TranslateRxTxNode(ros::NodeHandle &node, ros::NodeHandle &priv_nh)
  {
    pub_ = node.advertise<dataspeed_can_msgs::CanMessage>("can_tx", 100);
    sub_ = node.subscribe("can_rx", 100, &TranslateRxTxNode::recv, this, ros::TransportHints().tcpNoDelay(true));
  }
  ~TranslateRxTxNode() {}

private:
  void recv(const dataspeed_can_msgs::CanMessageStamped::ConstPtr& msg)
  {
    pub_.publish(msg->msg);
  }

  // Subscribed topics
  ros::Subscriber sub_;

  // Published topics
  ros::Publisher pub_;
};

} // namespace dataspeed_can_tools

#endif // _TRANSLATE_RX_TX_H_
