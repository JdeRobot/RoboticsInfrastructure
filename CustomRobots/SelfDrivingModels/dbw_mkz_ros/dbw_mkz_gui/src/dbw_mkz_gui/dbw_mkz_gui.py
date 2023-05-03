#!/usr/bin/env python

import rospy
import os
import rospkg

from qt_gui.plugin import Plugin
from python_qt_binding.QtGui import QWidget
from python_qt_binding import loadUi
from rospy.topics import Publisher, Subscriber
from rospy.timer import Timer
from PyQt4.Qt import QTimer, QGraphicsScene, QBrush, QImage, QPixmap, QPalette, QColor
from std_msgs.msg import Float64, Bool, Empty
from dbw_mkz_msgs.msg import ThrottleCmd, ThrottleReport, BrakeCmd, BrakeReport, SteeringCmd, SteeringReport, GearCmd, GearReport
import std_msgs
from dbw_mkz_msgs.msg._Misc1Report import Misc1Report
from dbw_mkz_msgs.msg._TirePressureReport import TirePressureReport
from dbw_mkz_msgs.msg._FuelLevelReport import FuelLevelReport
from sensor_msgs.msg._NavSatFix import NavSatFix
import math
from sensor_msgs.msg._Imu import Imu

class MkzGui(Plugin):

    package_name = 'dbw_mkz_gui' # Name of ROS package
    ui_filename = 'dbw_mkz_gui.ui' # filename of the QT gui resource
    gui_object_name = 'MkzGui' # runtime name of the GUI plugin
    update_period = 100 # GUI update period in ms
    
    def __init__(self, context):
        self.initVariables()
        self.setupWidget(context)
        self.initGraphics()
        self.bindCallbacks()
        self.subscribeTopics()   
        self.advertiseTopics()
    
    def initVariables(self):
        self.rad_to_deg = 57.295779515
        
        # DBW reported values
        self.reported_throttle = 0
        self.reported_brake = 0
        self.reported_boo = False
        self.reported_steering = 0
        self.reported_gear = '--'
        
        # DBW commands
        self.throttle_cmd = 0
        self.brake_cmd = 0
        self.steering_cmd = 0
        
        # Steering wheel button states
        self.on_off_btn = False
        self.res_cncl_btn = False
        self.set_inc_btn = False
        self.set_dec_btn = False
        self.gap_inc_btn = False
        self.gap_dec_btn = False
        self.la_on_off_btn = False
        
        # Message RX status
        self.throttle_stamp = rospy.Time()
        self.brake_stamp = rospy.Time()
        self.steering_stamp = rospy.Time()
        self.gear_stamp = rospy.Time()
        self.misc_stamp = rospy.Time()
        
        # Vehicle data labels
        self.gps_lat = 0
        self.gps_lon = 0
        self.speed = 0
        self.fl_tire = 0
        self.fr_tire = 0
        self.rl_tire = 0
        self.rr_tire = 0
        self.yaw_rate = 0
        self.roll_rate = 0
        self.fuel = 0
        
        # Report gear name map
        self.gear_map = []
        self.gear_map.append('None')
        self.gear_map.append('Park')
        self.gear_map.append('Reverse')
        self.gear_map.append('Neutral')
        self.gear_map.append('Drive')
        self.gear_map.append('Low')
        
        # Throttle faults
        self.throttle_driver = False
        self.throttle_flt1 = False
        self.throttle_flt2 = False
        self.throttle_fltcon = False
        
        # Brake faults
        self.brake_driver = False
        self.brake_flt1 = False
        self.brake_flt2 = False
        self.brake_fltboo = False
        self.brake_fltcon = False
        
        # Steering faults
        self.steering_driver = False
        self.steering_flt1 = False
        self.steering_flt2 = False
        self.steering_fltcon = False
        
        # Gear faults
        self.gear_driver = False
        self.gear_fltbus = False
        
    def updateGuiCallback(self):
        current_time = rospy.Time.now()
        
        # DBW system commands and reports
        self._widget.throttle_report_lbl.setText(str(self.reported_throttle))
        self._widget.brake_report_lbl.setText(str(self.reported_brake))
        self._widget.steering_report_lbl.setText(str(self.reported_steering))
        self._widget.gear_report_lbl.setText(self.reported_gear) 
        
        self._widget.throttle_cmd_lbl.setText(str(self.throttle_cmd))
        self._widget.brake_cmd_lbl.setText(str(self.brake_cmd))
        self._widget.steering_cmd_lbl.setText(str(self.steering_cmd))
        
        # Steering wheel buttons  
        if (current_time - self.misc_stamp) < rospy.Duration(0.25):
            if self.res_cncl_btn:
                self._widget.res_cncl_led.setPalette(self.green_palette)
            else:        
                self._widget.res_cncl_led.setPalette(self.red_palette)  
                
            if self.on_off_btn:
                self._widget.on_off_led.setPalette(self.green_palette)
            else:        
                self._widget.on_off_led.setPalette(self.red_palette)
                
            if self.set_inc_btn:
                self._widget.set_inc_led.setPalette(self.green_palette)
            else:        
                self._widget.set_inc_led.setPalette(self.red_palette)
                
            if self.set_dec_btn:
                self._widget.set_dec_led.setPalette(self.green_palette)
            else:        
                self._widget.set_dec_led.setPalette(self.red_palette)
                
            if self.gap_inc_btn:
                self._widget.gap_inc_led.setPalette(self.green_palette)
            else:        
                self._widget.gap_inc_led.setPalette(self.red_palette)
                
            if self.gap_dec_btn:
                self._widget.gap_dec_led.setPalette(self.green_palette)
            else:        
                self._widget.gap_dec_led.setPalette(self.red_palette)
    
            if self.la_on_off_btn:
                self._widget.la_on_off_led.setPalette(self.green_palette)
            else:        
                self._widget.la_on_off_led.setPalette(self.red_palette)
        else:
            self._widget.on_off_led.setPalette(self.gray_palette)
            self._widget.res_cncl_led.setPalette(self.gray_palette)
            self._widget.set_inc_led.setPalette(self.gray_palette)
            self._widget.set_dec_led.setPalette(self.gray_palette)
            self._widget.gap_inc_led.setPalette(self.gray_palette)
            self._widget.gap_dec_led.setPalette(self.gray_palette)
            self._widget.la_on_off_led.setPalette(self.gray_palette)
            
        # Report RX status LEDs
        if (current_time - self.throttle_stamp) < rospy.Duration(0.25):
            self._widget.throttle_led.setPalette(self.green_palette)
        else:
            self._widget.throttle_led.setPalette(self.red_palette)

        if (current_time - self.brake_stamp) < rospy.Duration(0.25):
            self._widget.brake_led.setPalette(self.green_palette)
        else:
            self._widget.brake_led.setPalette(self.red_palette)
            
        if (current_time - self.steering_stamp) < rospy.Duration(0.25):
            self._widget.steering_led.setPalette(self.green_palette)
        else:
            self._widget.steering_led.setPalette(self.red_palette)
            
        if (current_time - self.gear_stamp) < rospy.Duration(0.25):
            self._widget.gear_led.setPalette(self.green_palette)
        else:
            self._widget.gear_led.setPalette(self.red_palette)
            
        # Throttle faults
        if (current_time - self.throttle_stamp) < rospy.Duration(0.25):
            if self.throttle_driver:
                self._widget.throttle_driver_led.setPalette(self.yellow_palette)
            else:
                self._widget.throttle_driver_led.setPalette(self.green_palette)
            
            if self.throttle_flt1:
                self._widget.throttle_flt1_led.setPalette(self.red_palette)
            else:
                self._widget.throttle_flt1_led.setPalette(self.green_palette)
                
            if self.throttle_flt2:
                self._widget.throttle_flt2_led.setPalette(self.red_palette)
            else:
                self._widget.throttle_flt2_led.setPalette(self.green_palette)
                
            if self.throttle_fltcon:
                self._widget.throttle_fltcon_led.setPalette(self.red_palette)
            else:
                self._widget.throttle_fltcon_led.setPalette(self.green_palette)
        else:
            self._widget.throttle_driver_led.setPalette(self.gray_palette)
            self._widget.throttle_flt1_led.setPalette(self.gray_palette)
            self._widget.throttle_flt2_led.setPalette(self.gray_palette)
            self._widget.throttle_fltcon_led.setPalette(self.gray_palette)
            
        # Brake faults
        if (current_time - self.brake_stamp) < rospy.Duration(0.25):
            if self.brake_driver:
                self._widget.brake_driver_led.setPalette(self.yellow_palette)
            else:
                self._widget.brake_driver_led.setPalette(self.green_palette)    
     
            if self.brake_flt1:
                self._widget.brake_flt1_led.setPalette(self.red_palette)
            else:
                self._widget.brake_flt1_led.setPalette(self.green_palette) 
    
            if self.brake_flt2:
                self._widget.brake_flt2_led.setPalette(self.red_palette)
            else:
                self._widget.brake_flt2_led.setPalette(self.green_palette)
                            
            if self.brake_fltcon:
                self._widget.brake_fltcon_led.setPalette(self.red_palette)
            else:
                self._widget.brake_fltcon_led.setPalette(self.green_palette) 
                
            if self.brake_fltboo:
                self._widget.brake_fltb_led.setPalette(self.red_palette)
            else:
                self._widget.brake_fltb_led.setPalette(self.green_palette) 
        else:
            self._widget.brake_driver_led.setPalette(self.gray_palette)
            self._widget.brake_flt1_led.setPalette(self.gray_palette)
            self._widget.brake_flt2_led.setPalette(self.gray_palette)
            self._widget.brake_fltcon_led.setPalette(self.gray_palette)
            self._widget.brake_fltb_led.setPalette(self.gray_palette)
            
        # Steering faults
        if (current_time - self.steering_stamp) < rospy.Duration(0.25):
            if self.steering_driver:
                self._widget.steering_driver_led.setPalette(self.yellow_palette)
            else:
                self._widget.steering_driver_led.setPalette(self.green_palette)
                
            if self.steering_flt1:
                self._widget.steering_flt1_led.setPalette(self.red_palette)
            else:
                self._widget.steering_flt1_led.setPalette(self.green_palette)      
                
            if self.steering_flt2:
                self._widget.steering_flt2_led.setPalette(self.red_palette)
            else:
                self._widget.steering_flt2_led.setPalette(self.green_palette) 
                
            if self.steering_fltcon:
                self._widget.steering_fltcon_led.setPalette(self.red_palette)
            else:
                self._widget.steering_flt2_led.setPalette(self.green_palette)                 
        else:
            self._widget.steering_driver_led.setPalette(self.gray_palette)
            self._widget.steering_flt1_led.setPalette(self.gray_palette)
            self._widget.steering_flt2_led.setPalette(self.gray_palette)
            self._widget.steering_fltcon_led.setPalette(self.gray_palette)
            
        # Gear faults
        if (current_time - self.gear_stamp) < rospy.Duration(0.25):
            if self.gear_driver:
                self._widget.gear_driver_led.setPalette(self.yellow_palette)
            else:
                self._widget.gear_driver_led.setPalette(self.green_palette)
                
            if self.gear_fltbus:
                self._widget.gear_fltbus_led.setPalette(self.red_palette)
            else:
                self._widget.gear_fltbus_led.setPalette(self.green_palette)                        
        else:
            self._widget.gear_driver_led.setPalette(self.gray_palette)
            self._widget.gear_fltbus_led.setPalette(self.gray_palette)

        # Vehicle data labels
        self._widget.lat_lbl.setText(str(self.gps_lat))
        self._widget.lon_lbl.setText(str(self.gps_lon))
        self._widget.speed_lbl.setText(str(self.speed) + ' m/s')
        self._widget.fl_pressure_lbl.setText(str(self.fl_tire))
        self._widget.fr_pressure_lbl.setText(str(self.fr_tire))
        self._widget.rl_pressure_lbl.setText(str(self.rl_tire))   
        self._widget.rr_pressure_lbl.setText(str(self.rr_tire))
        self._widget.yaw_rate_lbl.setText(str(self.yaw_rate) + ' rad/s')
        self._widget.roll_rate_lbl.setText(str(self.roll_rate) + ' rad/s')
        self._widget.fuel_lbl.setText(str(self.fuel) + ' %')
        
        if self.reported_boo:
            self._widget.boo_led.setPalette(self.red_palette)
        else:
            self._widget.boo_led.setPalette(self.gray_palette)
    
        # Steering wheel buttons
        if self.on_off_btn:
            self._widget.on_off_led.setPalette(self.green_palette)
        else:
            self._widget.on_off_led.setPalette(self.gray_palette)
    
        if self.res_cncl_btn:
            self._widget.res_cncl_led.setPalette(self.green_palette)
        else:
            self._widget.res_cncl_led.setPalette(self.gray_palette)    

        if self.set_inc_btn:
            self._widget.set_inc_led.setPalette(self.green_palette)
        else:
            self._widget.set_inc_led.setPalette(self.gray_palette)     
    
        if self.set_dec_btn:
            self._widget.set_dec_led.setPalette(self.green_palette)
        else:
            self._widget.set_dec_led.setPalette(self.gray_palette)  
            
        if self.gap_inc_btn:
            self._widget.gap_inc_led.setPalette(self.green_palette)
        else:
            self._widget.gap_inc_led.setPalette(self.gray_palette)           
    
        if self.gap_dec_btn:
            self._widget.gap_dec_led.setPalette(self.green_palette)
        else:
            self._widget.gap_dec_led.setPalette(self.gray_palette)
            
        if self.la_on_off_btn:
            self._widget.la_on_off_led.setPalette(self.green_palette)
        else:
            self._widget.la_on_off_led.setPalette(self.gray_palette)           
                
    def initGraphics(self):
        
        # LED color palettes
        self.green_palette = QPalette()
        self.green_palette.setColor(QPalette.Window, QColor(0,255,0))

        self.red_palette = QPalette()
        self.red_palette.setColor(QPalette.Window, QColor(255,0,0))
        
        self.yellow_palette = QPalette()
        self.yellow_palette.setColor(QPalette.Window, QColor(200, 200, 50))        
        
        self.gray_palette = QPalette()
        self.gray_palette.setColor(QPalette.Window, QColor(80, 80, 80))
        
        # CAN RX LEDs
        self._widget.throttle_led.setText('')
        self._widget.throttle_led.setPalette(self.red_palette)
        self._widget.brake_led.setText('')
        self._widget.brake_led.setPalette(self.red_palette)
        self._widget.steering_led.setText('')
        self._widget.steering_led.setPalette(self.red_palette)
        self._widget.gear_led.setText('')
        self._widget.gear_led.setPalette(self.red_palette)
        
        # BOO LED
        self._widget.boo_led.setText('')
        self._widget.boo_led.setPalette(self.gray_palette)
        
        # Fault and driver override LEDs
        self._widget.throttle_driver_led.setText('')
        self._widget.throttle_driver_led.setPalette(self.gray_palette)
        self._widget.throttle_flt1_led.setText('')
        self._widget.throttle_flt1_led.setPalette(self.gray_palette)
        self._widget.throttle_flt2_led.setText('')
        self._widget.throttle_flt2_led.setPalette(self.gray_palette)
        self._widget.throttle_fltcon_led.setText('')
        self._widget.throttle_fltcon_led.setPalette(self.gray_palette)         
        
        self._widget.brake_driver_led.setText('')
        self._widget.brake_driver_led.setPalette(self.gray_palette)
        self._widget.brake_flt1_led.setText('')
        self._widget.brake_flt1_led.setPalette(self.gray_palette)
        self._widget.brake_flt2_led.setText('')
        self._widget.brake_flt2_led.setPalette(self.gray_palette)
        self._widget.brake_fltcon_led.setText('')
        self._widget.brake_fltcon_led.setPalette(self.gray_palette)         
        self._widget.brake_fltb_led.setText('')
        self._widget.brake_fltb_led.setPalette(self.gray_palette)   
        
        self._widget.steering_driver_led.setText('')
        self._widget.steering_flt1_led.setText('')
        self._widget.steering_flt2_led.setText('')
        self._widget.steering_fltcon_led.setText('')
        
        self._widget.gear_driver_led.setText('')
        self._widget.gear_fltbus_led.setText('')    
        
        # Steering wheel buttons
        self._widget.on_off_led.setText('')
        self._widget.on_off_led.setPalette(self.gray_palette)  
        self._widget.res_cncl_led.setText('')
        self._widget.res_cncl_led.setPalette(self.gray_palette)  
        self._widget.set_inc_led.setText('')
        self._widget.set_inc_led.setPalette(self.gray_palette)  
        self._widget.set_dec_led.setText('')
        self._widget.set_dec_led.setPalette(self.gray_palette)  
        self._widget.gap_inc_led.setText('')
        self._widget.gap_inc_led.setPalette(self.gray_palette)  
        self._widget.gap_dec_led.setText('')
        self._widget.gap_dec_led.setPalette(self.gray_palette)  
        self._widget.la_on_off_led.setText('')
        self._widget.la_on_off_led.setPalette(self.gray_palette)
    
    def bindCallbacks(self):
        pass
    
    def subscribeTopics(self):
        rospy.Subscriber('vehicle/throttle_report', ThrottleReport, self.recvThrottleReport)
        rospy.Subscriber('vehicle/brake_report', BrakeReport, self.recvBrakeReport)
        rospy.Subscriber('vehicle/steering_report', SteeringReport, self.recvSteeringReport)
        rospy.Subscriber('vehicle/gear_report', GearReport, self.recvGearReport)
        rospy.Subscriber('vehicle/misc1_report', Misc1Report, self.recvMisc1Report)
        rospy.Subscriber('vehicle/tire_pressure_report', TirePressureReport, self.recvTirePressure)
        rospy.Subscriber('vehicle/fuel_level_report', FuelLevelReport, self.recvFuelLevel)
        rospy.Subscriber('vehicle/gps/fix', NavSatFix, self.recvGps)
        rospy.Subscriber('vehicle/imu/data_raw', Imu, self.recvImu)
    
    def recvImu(self, msg):
        self.yaw_rate = 1e-2 * math.floor(1e2 * msg.angular_velocity.z)
        self.roll_rate = 1e-2 * math.floor(1e2 * msg.angular_velocity.x)
    
    def recvGps(self, msg):
        self.gps_lat = 1e-6 * math.floor(1e6 * msg.latitude)
        self.gps_lon = 1e-6 * math.floor(1e6 * msg.longitude)
    
    def recvThrottleReport(self, msg):
        self.throttle_stamp = rospy.Time.now()
        self.reported_throttle = int(math.floor(100 * msg.pedal_output))
        self.throttle_cmd = int(math.floor(100 * msg.pedal_cmd))
        
        self.throttle_driver = msg.driver
        self.throttle_flt1 = msg.fault_ch1
        self.throttle_flt2 = msg.fault_ch2
        self.throttle_fltcon = msg.fault_connector
        
    def recvBrakeReport(self, msg):
        self.brake_stamp = rospy.Time.now()
        self.reported_brake = int(math.floor(100 * msg.pedal_output))
        self.brake_cmd = int(math.floor(100 * msg.pedal_cmd))
        self.reported_boo = msg.boo_output
        
        self.brake_driver = msg.driver
        self.brake_flt1 = msg.fault_ch1
        self.brake_flt2 = msg.fault_ch2
        self.brake_fltboo = msg.fault_boo
        self.brake_fltcon = msg.fault_connector
            
    def recvSteeringReport(self, msg):
        self.steering_stamp = rospy.Time.now()
        self.speed = 0.1 * math.floor(10 * msg.speed)
        self.reported_steering = 0.1 * math.floor(self.rad_to_deg * 10 * msg.steering_wheel_angle)
        self.steering_cmd = 0.1 * math.floor(self.rad_to_deg * 10 * msg.steering_wheel_angle_cmd)
        
        self.steering_driver = msg.driver
        self.steering_flt1 = msg.fault_bus1
        self.steering_flt2 = msg.fault_bus2
        self.steering_fltcon = msg.fault_connector
    
    def recvGearReport(self, msg):
        self.gear_stamp = rospy.Time.now()
        self.reported_gear = self.gear_map[msg.state.gear]

        self.gear_driver = msg.driver
        self.gear_fltbus = msg.fault_bus
        
    def recvMisc1Report(self, msg):
        self.on_off_btn = msg.btn_cc_on_off
        self.res_cncl_btn = msg.btn_cc_res_cncl
        self.set_inc_btn = msg.btn_cc_set_inc
        self.set_inc_btn = msg.btn_cc_set_dec
        self.set_inc_btn = msg.btn_cc_gap_inc
        self.set_inc_btn = msg.btn_cc_gap_dec
        self.set_inc_btn = msg.btn_la_on_off
    
    def advertiseTopics(self):
        pass
    
    def recvTirePressure(self, msg):
        self.fl_tire = msg.front_left
        self.fr_tire = msg.front_right
        self.rl_tire = msg.rear_left
        self.rr_tire = msg.rear_right
        
    def recvFuelLevel(self, msg):
        self.fuel = 0.1 * math.floor(10 * msg.fuel_level)
    
    def setupWidget(self, context):
        super(MkzGui, self).__init__(context)
        # Give QObjects reasonable names
        self.setObjectName(self.gui_object_name)

        # Create QWidget
        self._widget = QWidget()

        # Get path to UI file which should be in the "resource" folder of this package
        ui_file = os.path.join(rospkg.RosPack().get_path(self.package_name), 'resource', self.ui_filename)
        # Extend the widget with all attributes and children from UI file
        loadUi(ui_file, self._widget)
        # Give QObjects reasonable names
        self._widget.setObjectName(self.gui_object_name)
        # Add widget to the user interface
        context.add_widget(self._widget)
        
        # Set up a timer to update the GUI
        update_timer = QTimer(self._widget)
        update_timer.setInterval(self.update_period);
        update_timer.setSingleShot(False);
        update_timer.timeout.connect(lambda: self.updateGuiCallback())
        update_timer.start()
        
    def shutdown_plugin(self):
        pass

