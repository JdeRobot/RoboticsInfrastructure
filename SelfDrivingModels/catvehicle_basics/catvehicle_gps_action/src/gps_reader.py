#! /usr/bin/env python

import rospy
from sensor_msgs.msg import NavSatFix
#https://pypi.python.org/pypi/geopy
from geopy.distance import vincenty

"""
uint8 COVARIANCE_TYPE_UNKNOWN=0                                                                                                 
uint8 COVARIANCE_TYPE_APPROXIMATED=1                                                                                            
uint8 COVARIANCE_TYPE_DIAGONAL_KNOWN=2                                                                                          
uint8 COVARIANCE_TYPE_KNOWN=3                                                                                                   
std_msgs/Header header                                                                                                          
  uint32 seq                                                                                                                    
  time stamp                                                                                                                    
  string frame_id                                                                                                               
sensor_msgs/NavSatStatus status                                                                                                 
  int8 STATUS_NO_FIX=-1                                                                                                         
  int8 STATUS_FIX=0                                                                                                             
  int8 STATUS_SBAS_FIX=1                                                                                                        
  int8 STATUS_GBAS_FIX=2                                                                                                        
  uint16 SERVICE_GPS=1                                                                                                          
  uint16 SERVICE_GLONASS=2                                                                                                      
  uint16 SERVICE_COMPASS=4                                                                                                      
  uint16 SERVICE_GALILEO=8                                                                                                      
  int8 status                                                                                                                   
  uint16 service                                                                                                                
float64 latitude                                                                                                                
float64 longitude                                                                                                               
float64 altitude                                                                                                                
float64[9] position_covariance                                                                                                  
uint8 position_covariance_type
"""
class WayPoint():
    def __init__(self, latitude, longitude, altitude):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        
    def print_data(self):
        return "["+str(self.latitude)+","+str(self.longitude)+","+str(self.altitude)+"]"


class GpsClass(object):
    def __init__(self):
        self._sub = rospy.Subscriber('/fix', NavSatFix, self.callback)
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.testwaypoint = WayPoint(49.900090,8.899960,0.000000)
    
    def remove_noise(self,latitude,longitude,altitude):
        """
        The GPS have Noise, so the always alscilation digits are removed
        """
        return round(latitude,5),round(longitude,5),round(altitude,1)
    
    def callback(self,msg):
        self.latitude, self.longitude, self.altitude = self.remove_noise(msg.latitude, msg.longitude, msg.altitude)
        #rospy.loginfo('Origin [latitude,longitude,altitude]=[%f,%f,%f]', self.latitude, self.longitude, self.altitude)
        #rospy.loginfo('Waypoint [latitude,longitude,altitude]=[%f,%f,%f]', self.testwaypoint.latitude, self.testwaypoint.longitude, self.testwaypoint.altitude)
        #rospy.loginfo('Distance to WayPointTest=%f', self.distance_from_waypoint(self.testwaypoint))
    
    def distance_from_waypoint(self,waypoint):
        """
        Its calculated only with longitud and latitude, altitude oscilates too much for a coherent reading and 
        in this application there is no reason to bare in mind.
        """
        origin = (self.latitude, self.longitude)
        waypoint = (waypoint.latitude, waypoint.longitude)
        return vincenty(origin, waypoint).meters
    
    def get_current_gps_pos(self):
        """
        Returns newest GPS current position in a Waypoint Format
        """
        return WayPoint(self.latitude, self.longitude, self.altitude)
        

if __name__ == '__main__':
  rospy.init_node('gps_topic_subscriber')
  GpsClass()
  rospy.spin()
