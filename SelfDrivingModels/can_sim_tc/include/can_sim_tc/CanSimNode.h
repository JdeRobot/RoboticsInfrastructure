#ifndef _CANSIM_NODE_H_
#define _CANSIM_NODE_H_

#include <ros/ros.h>
#include <ros/console.h>
#include <dbw_mkz_can/DbwNode.h>
#include <dbw_mkz_can/dispatch.h>
#include <dataspeed_can_msgs/CanMessageStamped.h>
#include <geometry_msgs/Twist.h>
#include <geometry_msgs/TwistStamped.h>
#include <std_msgs/Float32.h>
#include <dbw_mkz_msgs/Gear.h>
#include <sensor_msgs/NavSatFix.h>
#include <geometry_msgs/Vector3Stamped.h>
#include <time.h>

/*
These typed structures try to keep track of how many bits of data are stored
that the data stored will not surpass
the 64bit of information that the BusCan DataField maximum
https://es.wikipedia.org/wiki/Bus_CAN
*/
typedef struct {
  uint8_t JCMD :3;
  uint8_t :4;
  uint8_t CLEAR :1;
} MsgJointState;


namespace can_sim_tc
{

class CanSimNode
{
public:
    CanSimNode(ros::NodeHandle &node, ros::NodeHandle &priv_nh);
    ~CanSimNode();

private:

    // Ackermann steering
    double acker_wheelbase_;
    double acker_track_;
    double steering_ratio_;

    // Variables to store topic data needed in other callbacks
    geometry_msgs::Vector3Stamped current_fixgps_velocity_;

    // Published topics
    ros::Publisher pub_can_;
    ros::Publisher pub_throttle_cmd_;
    ros::Publisher pub_brake_cmd_;
    ros::Publisher pub_steering_cmd_;
    ros::Publisher pub_gear_cmd_;

    // Subscribed topics
    ros::Subscriber sub_can_;
    ros::Subscriber sub_cmdvelsafe_;
    ros::Subscriber sub_fix_;
    ros::Subscriber sub_fixvel_;

    void recvCAN(const dataspeed_can_msgs::CanMessage::ConstPtr& msg);
    void recvCmdVelSafe(const geometry_msgs::TwistStamped::ConstPtr& msg);
    void recvFixGps(const sensor_msgs::NavSatFix::ConstPtr& msg);
    void recvFixVelGps(const geometry_msgs::Vector3Stamped::ConstPtr& msg);

};

} // namespace dbw_mkz_can

#endif // _CANSIM_NODE_H_
