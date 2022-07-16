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
import csv
from dbw_mkz_msgs.msg import ThrottleCmd, ThrottleReport, ThrottleInfoReport
from dbw_mkz_msgs.msg import GearReport, SteeringReport
from math import fabs

class ThrottleSweep:
    def __init__(self):
        rospy.init_node('throttle_sweep')
        
        # Variables for logging
        self.throttle_cmd = 0.0
        self.msg_throttle_report = ThrottleReport()
        self.msg_throttle_report_ready = False
        self.msg_throttle_info_report = ThrottleInfoReport()
        self.msg_throttle_info_report_ready = False

        # Other drive-by-wire variables
        self.msg_gear_report = GearReport()
        self.msg_gear_report_ready = False
        self.msg_steering_report = SteeringReport()
        self.msg_steering_report_ready = False

        # Parameters
        self.i = -1
        self.start = 0.15
        self.end = 0.80
        self.resolution = 0.001
        self.duration = rospy.Duration(1.5)
        rospy.loginfo('Recording throttle pedal data every ' + str(self.duration.to_sec()) + ' seconds from ' + str(self.start) + ' to ' + str(self.end) + ' with ' + str(self.resolution) + ' increments.')
        rospy.loginfo('This will take '  + str((self.end - self.start) / self.resolution * self.duration.to_sec() / 60.0) + ' minutes.')

        # Open CSV file
        self.csv_file = open('throttle_sweep_data.csv', 'w')
        self.csv_writer = csv.writer(self.csv_file, delimiter=',')
        self.csv_writer.writerow(['Throttle (%)', 'Measured (%)'])
        
        # Publishers and subscribers
        self.pub = rospy.Publisher('/vehicle/throttle_cmd', ThrottleCmd, queue_size=1)
        rospy.Subscriber('/vehicle/throttle_report', ThrottleReport, self.recv_throttle)
        rospy.Subscriber('/vehicle/throttle_info_report', ThrottleInfoReport, self.recv_throttle_info)
        rospy.Subscriber('/vehicle/gear_report', GearReport, self.recv_gear)
        rospy.Subscriber('/vehicle/steering_report', SteeringReport, self.recv_steering)
        rospy.Timer(rospy.Duration(0.02), self.timer_cmd)
        rospy.Timer(self.duration, self.timer_process)

    def timer_process(self, event):
        if self.i < 0:
            # Check for safe conditions
            if not self.msg_steering_report_ready:
                rospy.logerr('Speed check failed. No messages on topic \'/vehicle/steering_report\'')
                rospy.signal_shutdown('')
            if self.msg_steering_report.speed > 1.0:
                rospy.logerr('Speed check failed. Vehicle speed is greater than 1 m/s.')
                rospy.signal_shutdown('')
            if not self.msg_gear_report_ready:
                rospy.logerr('Gear check failed. No messages on topic \'/vehicle/gear_report\'')
                rospy.signal_shutdown('')
            if not self.msg_gear_report.state.gear == self.msg_gear_report.state.PARK:
                rospy.logerr('Gear check failed. Vehicle not in park.')
                rospy.signal_shutdown('')
        elif self.i < int((self.end - self.start) / self.resolution + 1):
            # Check for new messages
            if not self.msg_throttle_report_ready:
                rospy.logerr('No new messages on topic \'/vehicle/throttle_report\'')
                rospy.signal_shutdown('')
            if not self.msg_throttle_info_report_ready:
                rospy.logerr('No new messages on topic \'/vehicle/throttle_info_report\'')
                rospy.signal_shutdown('')
            if not self.msg_throttle_report.enabled:
                rospy.logerr('Throttle module not enabled!')
                rospy.signal_shutdown('')

            # Make sure values are close to expected
            diff = self.throttle_cmd - self.msg_throttle_report.pedal_output
            if (fabs(diff) > 0.01):
                rospy.logwarn('Not saving data point. Large disparity between pedal request and actual: ' + str(diff))
            else:
                # Write data to file
                rospy.loginfo('Data point: ' + "{:.03f}".format(self.msg_throttle_report.pedal_output) + ', ' +
                                               "{:.03f}".format(self.msg_throttle_info_report.throttle_pc))
                self.csv_writer.writerow(["{:.03f}".format(self.msg_throttle_report.pedal_output),
                                          "{:.03f}".format(self.msg_throttle_info_report.throttle_pc)])
        else:
            rospy.signal_shutdown('')
        
        # Prepare for next iteration
        self.i += 1
        self.msg_throttle_report_ready = False
        self.msg_throttle_info_report_ready = False
        self.throttle_cmd = self.start + self.i * self.resolution

    def timer_cmd(self, event):
        if self.throttle_cmd > 0:
            msg = ThrottleCmd()
            msg.enable = True
            msg.pedal_cmd_type = ThrottleCmd.CMD_PEDAL
            msg.pedal_cmd = self.throttle_cmd
            self.pub.publish(msg)

    def recv_throttle(self, msg):
        self.msg_throttle_report = msg
        self.msg_throttle_report_ready = True

    def recv_throttle_info(self, msg):
        self.msg_throttle_info_report = msg
        self.msg_throttle_info_report_ready = True

    def recv_gear(self, msg):
        self.msg_gear_report = msg
        self.msg_gear_report_ready = True

    def recv_steering(self, msg):
        self.msg_steering_report = msg
        self.msg_steering_report_ready = True

    def shutdown_handler(self):
        rospy.loginfo('Saving csv file')
        self.csv_file.close()

if __name__ == '__main__':
    try:
        node = ThrottleSweep()
        rospy.on_shutdown(node.shutdown_handler)
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
