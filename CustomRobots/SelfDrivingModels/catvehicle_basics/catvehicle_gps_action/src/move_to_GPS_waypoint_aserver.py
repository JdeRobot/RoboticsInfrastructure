#! /usr/bin/env python
import rospy
import actionlib
from gps_reader import GpsClass, WayPoint
from actionlib.msg import TestFeedback, TestResult, TestAction
"""
### Test.action ###
int32 goal                                                                                                                      
---                                                                                                                             
int32 result                                                                                                                    
---                                                                                                                             
int32 feedback # This will give the distance from current pos to waypoint
"""

class MoveToGpsWayPointAServerClass(object):

  def __init__(self):
    # creates the action server
    rospy.init_node('move_to_gps_waypoint_aserver_node')
    # create messages that are used to publish feedback/result
    self._feedback = TestFeedback()
    self._result   = TestResult()
    # init some internal constants
    self._distance_error = 3.0 # A 3 metre error
    self._action_rate = 10.0
    waypoint1 = WayPoint(49.900090,8.899960,0.000000)
    self._waypoint_dict = {1:waypoint1}
    self._gps_class = GpsClass()
    self._as = actionlib.SimpleActionServer("/move_to_gps_waypoint_aserver", TestAction, self.goal_callback, False)
    self._as.start()
    rospy.loginfo('move_to_gps_waypoint_aserver initialised')

    
  def goal_callback(self, goal):
    # this callback is called when the action server is called.
    # this is the function that reads the GPS current position and publishes the appropriate Movement Command
    
    # helper variables
    r = rospy.Rate(self._action_rate)
    success = True
    
    # TODO: Fetch Data from topic GPS
    
    waypoint_gps_pos = self._waypoint_dict.get(goal.goal)
    if waypoint_gps_pos != None:
        
        # Distance from current pos to the given waypoint
        distance = self._gps_class.distance_from_waypoint(waypoint_gps_pos)
        self._feedback.feedback = int(distance)
        self._as.publish_feedback(self._feedback)
        
        start_gps_pos = self._gps_class.get_current_gps_pos()
        # publish info to the console for the user
        rospy.loginfo("#### move_to_gps_waypoint_as:\nStart GPS Position="+ str(start_gps_pos.print_data()) + "\nWayPoint = "+str(waypoint_gps_pos.print_data()) + "\nDistance ="+str(distance)+"\n###")
        
        # starts Moving To the WayPoint
        while int(distance) >= int(self._distance_error):
          rospy.loginfo('Distance From WayPoint:'+str(distance))
          # check that preempt (cancelation) has not been requested by the action client
          if self._as.is_preempt_requested():
            rospy.loginfo('The WayPoint has been cancelled/preempted')
            # the following line, sets the client in preempted state (goal cancelled)
            self._as.set_preempted()
            success = False
            self._result.result = int(success)
            break
          
          # builds the next feedback msg to be sent
          self._feedback.feedback = int(distance)
          # publish the feedback
          self._as.publish_feedback(self._feedback)
          # the sequence is computed at 1 Hz frequency
          r.sleep()
          
          # Update Distance
          distance = self._gps_class.distance_from_waypoint(waypoint_gps_pos)
    
    else:
        success = False
    # at this point, either the goal has been achieved (success==true)
    # or the client preempted the goal (success==false)
    # If success, then we publish the final result
    # If not success, we do not publish anything in the result
    if success:
        rospy.loginfo("### move_to_gps_waypoint_as:\nSucceeded to move from GPS Position="+ str(start_gps_pos.print_data()) + "\nWayPoint = "+str(waypoint_gps_pos.print_data())+"\n###")
        rospy.loginfo('Distance From WayPoint:'+str(distance)+",feedbackdistance="+str(self._feedback.feedback))
    else:
        rospy.loginfo("move_to_gps_waypoint_as: Failed")
    
    self._result.result = int(success)
    self._as.set_succeeded(self._result)
      
if __name__ == '__main__':
  
  MoveToGpsWayPointAServerClass()
  rospy.spin()