#include <can_sim_tc/CanSimNode.h>


namespace can_sim_tc
{

CanSimNode::CanSimNode(ros::NodeHandle &node, ros::NodeHandle &priv_nh)
{
    ROS_DEBUG("Created  %s", "CanSimNode");

    // SetUp Parametres
    // Ackermann steering parameters
    priv_nh.getParam("ackermann_wheelbase", acker_wheelbase_);
    priv_nh.getParam("ackermann_track", acker_track_);
    priv_nh.getParam("steering_ratio", steering_ratio_);

    ROS_DEBUG("Param server::CanSim :: ackermann_wheelbase  %f", acker_wheelbase_);
    ROS_DEBUG("Param server::CanSim :: ackermann_track  %f", acker_track_);
    ROS_DEBUG("Param server::CanSim :: steering_ratio  %f", steering_ratio_);

    // Initialise variables
    current_fixgps_velocity_.header.stamp = ros::Time::now();
    current_fixgps_velocity_.header.seq++;
    current_fixgps_velocity_.vector.x = 0.0;
    current_fixgps_velocity_.vector.y = 0.0;
    current_fixgps_velocity_.vector.z = 0.0;


    // Set up Publishers
    pub_can_ = node.advertise<dataspeed_can_msgs::CanMessageStamped>("can_rx", 10);
    pub_throttle_cmd_ = node.advertise<std_msgs::Float32>("/buscan_data/throttle_cmd", 0);
    pub_brake_cmd_ = node.advertise<std_msgs::Float32>("/buscan_data/brake_cmd", 0);
    pub_steering_cmd_ = node.advertise<std_msgs::Float32>("/buscan_data/steering_cmd", 0);
    pub_gear_cmd_ = node.advertise<dbw_mkz_msgs::Gear>("/buscan_data/gear_cmd", 0);

    // Set up Subscribers
    sub_can_ = node.subscribe("can_tx", 100, &CanSimNode::recvCAN, this, ros::TransportHints().tcpNoDelay(true));
    sub_cmdvelsafe_ = node.subscribe("/cmd_vel_safe", 1, &CanSimNode::recvCmdVelSafe, this, ros::TransportHints().tcpNoDelay(true));
    sub_fix_ = node.subscribe("/fix", 1, &CanSimNode::recvFixGps, this, ros::TransportHints().tcpNoDelay(true));
    sub_fixvel_ = node.subscribe("/fix_velocity", 1, &CanSimNode::recvFixVelGps, this, ros::TransportHints().tcpNoDelay(true));

}

CanSimNode::~CanSimNode()
{
    ROS_DEBUG("Destroyed  %s", "CanSimNode");
}


void CanSimNode::recvCAN(const dataspeed_can_msgs::CanMessage::ConstPtr& msg)
{

  if (!msg->extended) {
    switch (msg->id) {
        default:
            ROS_INFO("Message Id from CAN %i", msg->id);
        case ID_THROTTLE_CMD:
        if (msg->dlc >= sizeof(MsgThrottleCmd)) {
            const MsgThrottleCmd *ptr = (const MsgThrottleCmd*)msg->data.elems;
            const uint16_t throttle_pedal_buscan_value = ptr->PCMD;
            // We have to devide by this constant because the sender multiplies by it.
            const float converted_throttle_pedal_value = (float)throttle_pedal_buscan_value / UINT16_MAX;

            std_msgs::Float32 throttle_pedal_value;
            throttle_pedal_value.data = converted_throttle_pedal_value;
            pub_throttle_cmd_.publish(throttle_pedal_value);
        
        }
        break;
        
        case ID_BRAKE_CMD:
        if (msg->dlc >= sizeof(MsgBrakeCmd)) {
            const MsgBrakeCmd *ptr = (const MsgBrakeCmd*)msg->data.elems;
            
            const uint16_t brake_pedal_buscan_value = ptr->PCMD;
            // We have to devide by this constant because the sender multiplies by it.
            const float converted_brake_pedal_value = (float)brake_pedal_buscan_value / UINT16_MAX;
        
            std_msgs::Float32 brake_pedal_value;
            brake_pedal_value.data = converted_brake_pedal_value;
            pub_brake_cmd_.publish(brake_pedal_value);
        
        }
        break;
        
        case ID_STEERING_CMD:
        if (msg->dlc >= sizeof(MsgSteeringCmd)) {
            const MsgSteeringCmd *ptr = (const MsgSteeringCmd*)msg->data.elems;
            
            const int16_t steering_wheel_angle_buscan_value = ptr->SCMD;
            //const float converted_steering_wheel_angle_value = (float)steering_wheel_angle_buscan_value / INT16_MAX;
            const float converted_steering_wheel_angle_value = (float)steering_wheel_angle_buscan_value * (M_PI / 180) * 0.1;
        
            
            // The Data sent in BusCan Encoded is in Degrees and multiplied by 10 to not lose a the first decimal in the integer conversion.
            // Here we convert from Degrees to radians and divide by 10
            //const float radian_steering_angle = converted_steering_wheel_angle_value * (0.1 * M_PI / 180);
        
            
            std_msgs::Float32 steering_wheel_value;
            steering_wheel_value.data = converted_steering_wheel_angle_value;
            pub_steering_cmd_.publish(steering_wheel_value);
        
        }
        break;
        
        
        case ID_GEAR_CMD:
        if (msg->dlc >= sizeof(MsgGearCmd)) {
            const MsgGearCmd *ptr = (const MsgGearCmd*)msg->data.elems;
            
            const uint8_t gear_buscan_value = ptr->GCMD;
            
            dbw_mkz_msgs::Gear gear_msg;
            gear_msg.gear = gear_buscan_value;
            pub_gear_cmd_.publish(gear_msg);
        
        }
        break;
        
    
    }
  }

}


void CanSimNode::recvCmdVelSafe(const geometry_msgs::TwistStamped::ConstPtr& msg)
{
    dataspeed_can_msgs::CanMessageStamped out;
    out.msg.id = ID_STEERING_REPORT;
    out.msg.extended = false;
    // We have to use structures like the ones defined in distpatch.h
    out.msg.dlc = sizeof(MsgSteeringReport);

    out.header.stamp = msg->header.stamp;

    MsgSteeringReport *ptr = (MsgSteeringReport*)out.msg.data.elems;
    memset(ptr, 0x00, sizeof(*ptr));

    float steering_angle_speed = msg->twist.angular.z;
    float car_speed = msg->twist.linear.x;
    int angle_degree_buscan = 0;
    float f_angle_degree_buscan = 0.0;

    // Conversion that will be performed on the other side
    //twist.twist.angular.z = out.speed * tan(out.steering_wheel_angle / steering_ratio_) / acker_wheelbase_;

    f_angle_degree_buscan = atan((steering_angle_speed*acker_wheelbase_)/car_speed)*steering_ratio_*(180.0/(0.1*M_PI));
    angle_degree_buscan = int(f_angle_degree_buscan);
    ptr->ANGLE = angle_degree_buscan;

    // out.speed = (float)ptr->SPEED * (0.01 / 3.6);
    // Because the linear.x is already in m/s, we have to multiply by 3.6 to avoid distrtion in the conversion.
    ptr->SPEED = (int)(car_speed * 100 * 3.6);

    pub_can_.publish(out);

}

/*
sensor_msgs/NavSatFix
#####################
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
*/
void CanSimNode::recvFixGps(const sensor_msgs::NavSatFix::ConstPtr& msg)
{
    dataspeed_can_msgs::CanMessageStamped out1;
    dataspeed_can_msgs::CanMessageStamped out2;
    dataspeed_can_msgs::CanMessageStamped out3;
    
    out1.msg.id = ID_REPORT_GPS1;
    out2.msg.id = ID_REPORT_GPS2;
    out3.msg.id = ID_REPORT_GPS3;
    
    out1.msg.extended = false;
    out2.msg.extended = false;
    out3.msg.extended = false;
    
    // We have to use structures like the ones defined in distpatch.h
    out1.msg.dlc = sizeof(MsgReportGps1);
    out2.msg.dlc = sizeof(MsgReportGps2);
    out3.msg.dlc = sizeof(MsgReportGps3);

    out1.header.stamp = msg->header.stamp;
    out2.header.stamp = msg->header.stamp;
    out3.header.stamp = msg->header.stamp;

    MsgReportGps1 *ptr1 = (MsgReportGps1*)out1.msg.data.elems;
    MsgReportGps2 *ptr2 = (MsgReportGps2*)out2.msg.data.elems;
    MsgReportGps3 *ptr3 = (MsgReportGps3*)out3.msg.data.elems;
    
    memset(ptr1, 0x00, sizeof(*ptr1));
    memset(ptr2, 0x00, sizeof(*ptr2));
    memset(ptr3, 0x00, sizeof(*ptr3));

    float latitude = msg->latitude;
    float longitude = msg->longitude;
    float altitude = msg->altitude;
    
    // Conversions due to the other side, probably GPS models specifics and precission wanted.
    ptr1->latitude = (int)(latitude*3e6);
    ptr1->longitude = (int)(longitude*3e6);
    ptr3->altitude = (int)(altitude / 0.25);

    // For setting status to sensor_msgs::NavSatStatus::STATUS_FIX
    ptr3->quality = 2;

    float heading_angle_rad = atan(current_fixgps_velocity_.vector.y/current_fixgps_velocity_.vector.x);
    float heading_angle_degrees_100 = heading_angle_rad * (180.0 / M_PI ) * 100;
    ptr3->heading = (int)heading_angle_degrees_100;
    
    float speed_XY_magnitude = sqrt((current_fixgps_velocity_.vector.x*current_fixgps_velocity_.vector.x)+(current_fixgps_velocity_.vector.y*current_fixgps_velocity_.vector.y));
    ptr3->speed = int(speed_XY_magnitude / 0.44704);

    //std::time_t time_result = std::time(NULL);
    
    struct tm *theTime;
	time_t tim;
	time(&tim);
	theTime = localtime(&tim);
	int hours = theTime->tm_hour;
    
    ptr2->utc_year = (int)(theTime->tm_year - 100);
    ptr2->utc_month = (int)(theTime->tm_mon + 1);
    ptr2->utc_day = (int)theTime->tm_mday;
    ptr2->utc_hours = (int)theTime->tm_hour;
    ptr2->utc_minutes = (int)theTime->tm_min;
    ptr2->utc_seconds = (int)theTime->tm_sec;

    pub_can_.publish(out1);
    pub_can_.publish(out2);
    pub_can_.publish(out3);

}

/*
geometry_msgs/Vector3Stamped
############################
std_msgs/Header header                                                                                                          
  uint32 seq                                                                                                                    
  time stamp                                                                                                                    
  string frame_id                                                                                                               
geometry_msgs/Vector3 vector                                                                                                    
  float64 x                                                                                                                     
  float64 y                                                                                                                     
  float64 z
*/
void CanSimNode::recvFixVelGps(const geometry_msgs::Vector3Stamped::ConstPtr& msg)
{
    // Update the current gps speed message
    current_fixgps_velocity_.header.stamp = msg->header.stamp;
    current_fixgps_velocity_.header.seq = msg->header.seq;
    current_fixgps_velocity_.header.frame_id = msg->header.frame_id;
    current_fixgps_velocity_.vector.x = msg->vector.x;
    current_fixgps_velocity_.vector.y = msg->vector.y;
    current_fixgps_velocity_.vector.z = msg->vector.z;
    
    //ROS_INFO("Message Linear X Speed from /fix_velocity %f", current_fixgps_velocity_.vector.x);
}

} // namespace dbw_mkz_can
