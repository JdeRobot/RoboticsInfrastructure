#! /usr/bin/env python

import rospy
import time
import actionlib
from actionlib.msg import TestAction, TestGoal, TestResult, TestFeedback
"""
### Test.action ###
int32 goal                                                                                                                      
---                                                                                                                             
int32 result                                                                                                                    
---                                                                                                                             
int32 feedback # This will give the distance from current pos to waypoint
"""
"""
class SimpleGoalState:
    PENDING = 0
    ACTIVE = 1
    DONE = 2
    WARN = 3
    ERROR = 4

"""
# We create some constants with the corresponing vaules from the SimpleGoalState class
PENDING = 0
ACTIVE = 1
DONE = 2
WARN = 3
ERROR = 4

# definition of the feedback callback. This will be called when feedback
# is received from the action server
# it just prints a message indicating a new message has been received
def feedback_callback(feedback):
    rospy.loginfo('Feedback Distnace = '+str(feedback.feedback))

# initializes the action client node
rospy.init_node('move_to_gps_waypoint_aclient_node')

action_server_name = '/move_to_gps_waypoint_aserver'
client = actionlib.SimpleActionClient(action_server_name, TestAction)

# waits until the action server is up and running
rospy.loginfo('Waiting for action Server '+action_server_name)
client.wait_for_server()
rospy.loginfo('Action Server Found...'+action_server_name)

# creates a goal to send to the action server
goal = TestGoal()
goal.goal = 1 # indicates, move to waypoint number 1

client.send_goal(goal, feedback_cb=feedback_callback)


# You can access the SimpleAction Variable "simple_state", that will be 1 if active, and 2 when finished.
#Its a variable, better use a function like get_state.
#state = client.simple_state
# state_result will give the FINAL STATE. Will be 1 when Active, and 2 if NO ERROR, 3 If Any Warning, and 3 if ERROR
state_result = client.get_state()

rate = rospy.Rate(10)

rospy.loginfo("state_result: "+str(state_result))

while state_result < DONE:
    #rospy.loginfo("Doing Stuff while waiting for the Server to give a result....Nothing for the moment")
    rate.sleep()
    state_result = client.get_state()
    #rospy.loginfo("state_result: "+str(state_result))
    
rospy.loginfo("[Result] State: "+str(state_result))
if state_result == ERROR:
    rospy.logerr("Something went wrong in the Server Side")
if state_result == WARN:
    rospy.logwarn("There is a warning in the Server Side")
