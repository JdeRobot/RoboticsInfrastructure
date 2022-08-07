#!/usr/bin/env python
import rospy
from std_msgs.msg import String, Float64, Float32
from geometry_msgs.msg import Twist
from dbw_mkz_msgs.msg import Gear
import sys, getopt, math

class CarControToCmdVel(object):

    def __init__(self):
        rospy.init_node('car_controls_to_cmdvel', anonymous=True)

        self.MAX_BRAKE_VALUE = 0.5
        
        rospy.Subscriber('/buscan_data/throttle_cmd', Float32, self.throttle_callback)
        rospy.Subscriber('/buscan_data/brake_cmd', Float32, self.brake_callback)
        rospy.Subscriber('/buscan_data/steering_cmd', Float32, self.steering_callback)
        rospy.Subscriber('/buscan_data/gear_cmd', Gear, self.gear_callback)
        
        self.pub_cmdvel_safe = rospy.Publisher('/catvehicle/cmd_vel', Twist, queue_size=0)

        # initial velocity and tire angle are 0
        self.throttle = 0.0 # not pressed
        self.brake = 0.0 # not pressed
        self.steering = 0.0 # no steering
        self.gear = 1 # park

        # Time after which we consider a message too old
        self.timeout=rospy.Duration.from_sec(0.2);
        self.lastMsg_throttle=rospy.Time.now()
        self.lastMsg_brake=rospy.Time.now()
        self.lastMsg_steering=rospy.Time.now()
        self.lastMsg_gear=rospy.Time.now()

        
    def throttle_callback(self,msg):
        self.throttle = msg.data
        self.lastMsg_throttle = rospy.Time.now()
    
    def brake_callback(self,msg):
        self.brake = msg.data
        self.lastMsg_brake = rospy.Time.now()
        
    def steering_callback(self,msg):
        self.steering = msg.data
        self.lastMsg_steering = rospy.Time.now()
        
    def gear_callback(self,msg):
        self.gear = msg.gear
        self.lastMsg_gear = rospy.Time.now()


    def check_all_topics_are_old(self):
        throttle_delta_last_msg_time = rospy.Time.now() - self.lastMsg_throttle
        throttle_msgs_too_old = throttle_delta_last_msg_time > self.timeout
        
        brake_delta_last_msg_time = rospy.Time.now() - self.lastMsg_brake
        brake_msgs_too_old = brake_delta_last_msg_time > self.timeout
        
        steering_delta_last_msg_time = rospy.Time.now() - self.lastMsg_steering
        steering_msgs_too_old = steering_delta_last_msg_time > self.timeout
        
        gear_delta_last_msg_time = rospy.Time.now() - self.lastMsg_gear
        gear_msgs_too_old = gear_delta_last_msg_time > self.timeout

        return throttle_msgs_too_old and brake_msgs_too_old and steering_msgs_too_old and gear_msgs_too_old

    def publish(self):
        """
        This function will publish at a rate if all the critical topics are new.
        If any of them is not been published for a long time, it has to stop publishing inmediatelly until all are again published.
        The rules for the values are:
        1) The linear speed is the difference between the brake and the throttle. If the brake exceeds a value, the car will be stopped.
        2) The Gear only will affect the linear speed sign. D = 4 = positive, R = 2 = Negative, Rest = Lineare will be zero
        3) Steering corresponds to the angle of the ackerman fron imaginary wheel.
        """
        
        if self.check_all_topics_are_old():
            #rospy.loginfo("Some of the topics arent published fast enough, not publishing")
            return
        
        
        if self.gear == 4:
            gear_moder = 1
        elif self.gear == 2:
            gear_moder = -1
        else:
            gear_moder = 0
        
        
        if self.brake > self.MAX_BRAKE_VALUE:
            linear_speed = 0.0
        else:
            linear_speed = gear_moder * (self.throttle - self.brake)

        cmd_vel_msg = Twist()
        cmd_vel_msg.linear.x = linear_speed
        cmd_vel_msg.angular.z = self.steering
        self.pub_cmdvel_safe.publish(cmd_vel_msg)
        return
        

def main():
    car_control_to_cmdvel_object = CarControToCmdVel()
    rate = rospy.Rate(5) # run at 5Hz
    while not rospy.is_shutdown():
        car_control_to_cmdvel_object.publish()
        rate.sleep()

if __name__ == '__main__':
    
    try:
        main()
    except rospy.ROSInterruptException:
        pass


