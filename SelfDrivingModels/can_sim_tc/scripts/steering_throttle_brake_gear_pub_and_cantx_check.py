#!/usr/bin/env python
# license removed for brevity
import rospy
import random
from dbw_mkz_msgs.msg import BrakeCmd
from dbw_mkz_msgs.msg import ThrottleCmd
from dbw_mkz_msgs.msg import SteeringCmd
from dbw_mkz_msgs.msg import GearCmd, Gear
from dataspeed_can_msgs.msg import CanMessage
from std_msgs.msg import Empty

class CarControl(object):
    def __init__(self):
        self.pub_brake_cmd = rospy.Publisher('/vehicle/brake_cmd', BrakeCmd, queue_size=1)
        self.pub_throttle_cmd = rospy.Publisher('/vehicle/throttle_cmd', ThrottleCmd, queue_size=1)
        self.pub_steering_cmd = rospy.Publisher('/vehicle/steering_cmd', SteeringCmd, queue_size=1)
        self.pub_gear_cmd = rospy.Publisher('/vehicle/gear_cmd', GearCmd, queue_size=1)
        
        # We create this pub sub to check that the enable is sent, otherwise no publishing will be taken by dbw
        self._enable_dbw = False
        self.pub_enable = rospy.Publisher('/vehicle/enable', Empty, queue_size=1)
        sub = rospy.Subscriber("/vehicle/enable", Empty, self.enable_callback)
        self.enable_dbw_inputs_loop()
        
        # We wait for the Gazebo system to be available before publishing anything
        rospy.wait_for_service('/gazebo/set_physics_properties')
        rospy.loginfo("Gazebo Ready...")

    
    def enable_callback(self,data):
        self._enable_dbw = True

    def enable_dbw_inputs_loop(self):
        """
        We publish enable to enable dbw allow commands from outside
        rostopic pub /vehicle/enable std_msgs/Empty "{}"
        """
        rate = rospy.Rate(1)
        while not self._enable_dbw:
            rospy.loginfo("Try to enable /vehicle/enable, STATUS =  "+str(self._enable_dbw))
            self.enable_dbw_inputs()
            rate.sleep()
        rospy.loginfo("dbw inputs ENABLED...")

    def enable_dbw_inputs(self):
        
        empty_message = Empty()
        rospy.loginfo("Publish Enable Command in /vehicle/enable ")
        self.pub_enable.publish(empty_message)

    def cmd_publisher(self):
        """
        This makes the simulated function of all the basic controles of a car being used:
        brake, throttle, gear and steering_wheel.
        :return:
        """
        
        rate = rospy.Rate(5)
        speed = 1.0
        while not rospy.is_shutdown():
            rospy.loginfo("########### Starting CarControl Cmd Publish Round... ###########")
            self.throttle_cmd_publisher(throttle_value=speed)
            self.brake_cmd_publisher(brake_value=0.0)
            self.steering_cmd_publisher(angle_rad=0.0)
            self.gear_cmd_publisher(gear_value=4)
            rate.sleep()
            
    
    def throttle_cmd_publisher(self, throttle_value=0.0):
        """
        ID = 98 in BUSCAN
        # Throttle pedal
        # Options defined below
        float32 pedal_cmd
        uint8 pedal_cmd_type
        
        # Enable
        bool enable
        
        # Ignore driver overrides
        bool ignore
        
        # Watchdog counter (optional)
        uint8 count
        
        uint8 CMD_NONE=0
        uint8 CMD_PEDAL=1   # Unitless, range 0.15 to 0.80
        uint8 CMD_PERCENT=2 # Percent of maximum throttle, range 0 to 1
        """
        #msg_str = "Publishing Throttle message in /vehicle/throttle_cmd %s" % rospy.get_time()
        #rospy.loginfo(msg_str)
        throttle_command_object = ThrottleCmd()
        #throttle_command_object.pedal_cmd = random.uniform(0.15, 0.8)
        throttle_command_object.pedal_cmd = throttle_value
        throttle_command_object.pedal_cmd_type = 1
        throttle_command_object.enable = False
        throttle_command_object.ignore = False
        throttle_command_object.count = 0
        rospy.loginfo("Throttle Publish ::>"+str(throttle_command_object.pedal_cmd))
        self.pub_throttle_cmd.publish(throttle_command_object)
    
    def brake_cmd_publisher(self, brake_value=0.0):
        """
        ID = 96 in BusCan
        # Brake pedal
        # Options defined below
        float32 pedal_cmd
        uint8 pedal_cmd_type
        
        # Brake On Off (BOO), brake lights
        bool boo_cmd
        
        # Enable
        bool enable
        
        # Ignore driver overrides
        bool ignore
        
        # Watchdog counter (optional)
        uint8 count
        
        uint8 CMD_NONE=0
        uint8 CMD_PEDAL=1   # Unitless, range 0.15 to 0.50
        uint8 CMD_PERCENT=2 # Percent of maximum torque, range 0 to 1
        uint8 CMD_TORQUE=3  # Nm, range 0 to 3250
        
        float32 TORQUE_BOO=520  # Nm, brake lights threshold
        float32 TORQUE_MAX=3412 # Nm, maximum torque
        """
        #msg_str = "Publishing Brake message in /vehicle/brake_cmd %s" % rospy.get_time()
        #rospy.loginfo(msg_str)
        brake_command_object = BrakeCmd()
        #brake_command_object.pedal_cmd = random.uniform(0.15, 0.5)
        brake_command_object.pedal_cmd = brake_value
        brake_command_object.pedal_cmd_type = 1
        brake_command_object.boo_cmd = False
        brake_command_object.enable = False
        brake_command_object.ignore = False
        brake_command_object.count = 0
        rospy.loginfo("Brake Publish ::>"+str(brake_command_object.pedal_cmd))
        self.pub_brake_cmd.publish(brake_command_object)
    
    def steering_cmd_publisher(self, angle_rad=0.0):
        """
        ID = 100 in BusCan
        # Steering Wheel
        float32 steering_wheel_angle_cmd        # rad, range -8.2 to 8.2
        float32 steering_wheel_angle_velocity   # rad/s, range 0 to 8.7, 0 = maximum
        
        # Enable
        bool enable
        
        # Ignore driver overrides
        bool ignore
        
        # Disable the driver override audible warning
        bool quiet
        
        # Watchdog counter (optional)
        uint8 count
        """
        #msg_str = "Publishing Steering message in /vehicle/steering_cmd %s" % rospy.get_time()
        #rospy.loginfo(msg_str)
        steering_command_object = SteeringCmd()
        #steering_command_object.steering_wheel_angle_cmd = random.uniform(-8.2, 8.2)
        steering_command_object.steering_wheel_angle_cmd = angle_rad
        steering_command_object.steering_wheel_angle_velocity = random.uniform(0.0, 8.7)
        #steering_command_object.steering_wheel_angle_velocity = 0.8
        
        steering_command_object.enable = False
        steering_command_object.ignore = False
        steering_command_object.quiet = False
        steering_command_object.count = 0
        rospy.loginfo("Steering Publish ::>"+str(steering_command_object.steering_wheel_angle_cmd))
        self.pub_steering_cmd.publish(steering_command_object)
        
    def gear_cmd_publisher(self,gear_value=0):
        """
        ID = 102 in BusCan
        # Gear command enumeration
        Gear cmd
        >>>
        
        uint8 gear
        
        uint8 NONE=0
        uint8 PARK=1
        uint8 REVERSE=2
        uint8 NEUTRAL=3
        uint8 DRIVE=4
        uint8 LOW=5
        >>>
        
        gear is an uint8, but in the MsgGearCmd in dispatch.h only gets 3 Bits, which make up to
        8 (0-7) possible gears, which could be: 1,2,3,4,5,R,P,N.
        But in th emessage deffinition the only options given are None, Park, Reverse, Neutral, Drive and Low.
        so 6 options (0-5)
        """
        #msg_str = "Publishing Gear message in /vehicle/gear_cmd %s" % rospy.get_time()
        #rospy.loginfo(msg_str)
        gear_command_object = GearCmd()
        gear_object = Gear()
        #gear_object.gear = random.randint(0, 5)
        gear_object.gear = gear_value
        gear_command_object.cmd = gear_object
        rospy.loginfo("Gear Publish ::>"+str(gear_object.gear))
        self.pub_gear_cmd.publish(gear_command_object)
    



if __name__ == '__main__':
    rospy.init_node('sterring_throttle_brake_gear_publisher_node', anonymous=True)
    car_control_object = CarControl()
    try:
        car_control_object.cmd_publisher()
    except rospy.ROSInterruptException:
        print "Exception occured"
        pass