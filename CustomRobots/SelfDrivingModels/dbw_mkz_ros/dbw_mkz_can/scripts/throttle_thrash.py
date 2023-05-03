#!/usr/bin/env python

# Software License Agreement (BSD License)
#
# Copyright (c) 2014-2016, Dataspeed Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of Dataspeed Inc. nor the names of its
#       contributors may be used to endorse or promote products derived from this
#       software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd
from dbw_mkz_msgs.msg import GearReport, SteeringReport

class ThrottleThrash:
    def __init__(self):
        rospy.init_node('throttle_thrash')

        # Shutdown
        self.shutdown = False

        # Received messages
        self.dbw_enabled = False
        self.msg_steering_report_ready = False
        self.msg_gear_report = GearReport()
        self.msg_gear_report_ready = False
        self.msg_steering_report = SteeringReport()
        self.msg_steering_report_ready = False

        # Parameters
        self.started = False
        rospy.loginfo('Preparing to thrash the throttle pedal command to try and induce a fault...')
        rospy.loginfo('Validating that vehicle is parked...')

        # Command state
        self.cmd_state = False
        
        # Publishers and subscribers
        self.pub = rospy.Publisher('/vehicle/throttle_cmd', ThrottleCmd, queue_size=10)
        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.recv_enabled)
        rospy.Subscriber('/vehicle/gear_report', GearReport, self.recv_gear)
        rospy.Subscriber('/vehicle/steering_report', SteeringReport, self.recv_steering)
        rospy.Timer(rospy.Duration(0.2), self.timer_process)

    def timer_process(self, event):
        # Check for safe conditions
        if not self.msg_steering_report_ready:
            self.shutdown = True
            rospy.logerr('Speed check failed. No messages on topic \'/vehicle/steering_report\'')
        elif not self.msg_steering_report.speed == 0.0:
            self.shutdown = True
            rospy.logerr('Speed check failed. Vehicle speed is not zero.')
        if not self.msg_gear_report_ready:
            self.shutdown = True
            rospy.logerr('Gear check failed. No messages on topic \'/vehicle/gear_report\'')
        elif not self.msg_gear_report.state.gear == self.msg_gear_report.state.PARK:
            self.shutdown = True
            rospy.logerr('Gear check failed. Vehicle not in park.')

        # Check if enabled
        if self.shutdown:
            rospy.signal_shutdown('')
            return

        # Check if enabled
        if not self.dbw_enabled:
            rospy.logwarn('Drive-by-wire not enabled!')

        # Start command timers
        if not self.started:
            self.started = True
            rospy.Timer(rospy.Duration(0.020), self.timer_cmd)
            rospy.loginfo('Started thrashing the throttle pedal command to try and induce a fault.')
        
        # Prepare for next iteration
        self.msg_gear_report_ready = False
        self.msg_steering_report_ready = False

    def timer_cmd(self, event):
        if not self.shutdown:
            msg = ThrottleCmd()
            msg.enable = True
            msg.pedal_cmd_type = ThrottleCmd.CMD_PEDAL
            if self.cmd_state:
                msg.pedal_cmd = 1.0
            else:
                msg.pedal_cmd = 0.0
            self.pub.publish(msg)
            self.cmd_state = not self.cmd_state

    def recv_enabled(self, msg):
        self.dbw_enabled = msg.data

    def recv_gear(self, msg):
        self.msg_gear_report = msg
        self.msg_gear_report_ready = True

    def recv_steering(self, msg):
        self.msg_steering_report = msg
        self.msg_steering_report_ready = True

    def shutdown_handler(self):
        pass

if __name__ == '__main__':
    try:
        node = ThrottleThrash()
        rospy.on_shutdown(node.shutdown_handler)
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
