/*********************************************************************
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2015-2016, Dataspeed Inc.
 *  All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above
 *     copyright notice, this list of conditions and the following
 *     disclaimer in the documentation and/or other materials provided
 *     with the distribution.
 *   * Neither the name of Dataspeed Inc. nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 *  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 *  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 *  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 *  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 *  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 *  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 *  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 *  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 *********************************************************************/

//#include "DbwNode.h"
#include <dbw_mkz_can/DbwNode.h>
//#include "dispatch.h"
#include <dbw_mkz_can/dispatch.h>

namespace dbw_mkz_can
{

static const struct {float pedal; float torque;} BRAKE_TABLE[] = {
// Duty,   Nm
 {0.150,    0},
 {0.175,    0},
 {0.184,    4},
 {0.208,  108},
 {0.211,  519},
 {0.234,  521},
 {0.246,  816},
 {0.283, 1832},
 {0.305, 2612},
 {0.323, 3316},
 {0.326, 3412},
 {0.330, 3412},
};
static const struct {float pedal; float percent;} THROTTLE_TABLE[] = {
// Duty,   %
 {0.150, 0.000},
 {0.165, 0.001},
 {0.166, 0.020},
 {0.800, 1.000},
};
static inline float brakeTorqueFromPedal(float pedal) {
  const unsigned int size = sizeof(BRAKE_TABLE) / sizeof(BRAKE_TABLE[0]);
  if (pedal <= BRAKE_TABLE[0].pedal) {
    return BRAKE_TABLE[0].torque;
  } else if (pedal >= BRAKE_TABLE[size - 1].pedal) {
    return BRAKE_TABLE[size - 1].torque;
  } else {
    for (unsigned int i = 1; i < size; i++) {
      if (pedal < BRAKE_TABLE[i].pedal) {
        float start = BRAKE_TABLE[i - 1].torque;
        float dinput = pedal - BRAKE_TABLE[i - 1].pedal;
        float dtorque = BRAKE_TABLE[i].torque - BRAKE_TABLE[i - 1].torque;
        float dpedal = BRAKE_TABLE[i].pedal - BRAKE_TABLE[i - 1].pedal;
        if (fabsf(dpedal) > (float)1e-6) {
          return start + (dinput * dtorque / dpedal);
        } else {
          return start + (dtorque / 2);
        }
      }
    }
  }
  return 0.0;
}
static inline float brakePedalFromTorque(float torque) {
  const unsigned int size = sizeof(BRAKE_TABLE) / sizeof(BRAKE_TABLE[0]);
  if (torque <= BRAKE_TABLE[0].torque) {
    return BRAKE_TABLE[0].pedal;
  } else if (torque >= BRAKE_TABLE[size - 1].torque) {
    return BRAKE_TABLE[size - 1].pedal;
  } else {
    for (unsigned int i = 1; i < size; i++) {
      if (torque < BRAKE_TABLE[i].torque) {
        float start = BRAKE_TABLE[i - 1].pedal;
        float dinput = torque - BRAKE_TABLE[i - 1].torque;
        float dpedal = BRAKE_TABLE[i].pedal - BRAKE_TABLE[i - 1].pedal;
        float dtorque = BRAKE_TABLE[i].torque - BRAKE_TABLE[i - 1].torque;
        if (fabsf(dtorque) > (float)1e-6) {
          return start + (dinput * dpedal / dtorque);
        } else {
          return start + (dpedal / 2);
        }
      }
    }
  }
  return 0.0;
}
static inline float brakePedalFromPercent(float percent) {
  return brakePedalFromTorque(percent * BRAKE_TABLE[sizeof(BRAKE_TABLE) / sizeof(BRAKE_TABLE[0]) - 1].torque);
}
static inline float throttlePedalFromPercent(float percent) {
  const unsigned int size = sizeof(THROTTLE_TABLE) / sizeof(THROTTLE_TABLE[0]);
  if (percent <= THROTTLE_TABLE[0].percent) {
    return THROTTLE_TABLE[0].pedal;
  } else if (percent >= THROTTLE_TABLE[size - 1].percent) {
    return THROTTLE_TABLE[size - 1].pedal;
  } else {
    for (unsigned int i = 1; i < size; i++) {
      if (percent < THROTTLE_TABLE[i].percent) {
        float start = THROTTLE_TABLE[i - 1].pedal;
        float dinput = percent - THROTTLE_TABLE[i - 1].percent;
        float dpedal = THROTTLE_TABLE[i].pedal - THROTTLE_TABLE[i - 1].pedal;
        float dpercent = THROTTLE_TABLE[i].percent - THROTTLE_TABLE[i - 1].percent;
        if (fabsf(dpercent) > (float)1e-6) {
          return start + (dinput * dpedal / dpercent);
        } else {
          return start + (dpedal / 2);
        }
      }
    }
  }
  return 0.0;
}


static const struct {float x; float y; float z; float a;} SONAR_TABLE[] = {
//   x,      y,     z,     angle
 { 4.000,  0.900, 0.100, 0.500 * M_PI}, // Front left side
 { 4.000,  0.500, 0.100, 0.100 * M_PI}, // Front left corner
 { 4.000,  0.200, 0.100, 0.000 * M_PI}, // Front left center
 { 4.000, -0.200, 0.100, 0.000 * M_PI}, // Front right center
 { 4.000, -0.500, 0.100, 1.900 * M_PI}, // Front right corner
 { 4.000, -0.900, 0.100, 1.500 * M_PI}, // Front right side
 {-1.000,  0.900, 0.100, 0.500 * M_PI}, // Rear left side
 {-1.000,  0.500, 0.100, 0.900 * M_PI}, // Rear left corner
 {-1.000,  0.200, 0.100, 1.000 * M_PI}, // Rear left center
 {-1.000, -0.200, 0.100, 1.000 * M_PI}, // Rear right center
 {-1.000, -0.500, 0.100, 1.100 * M_PI}, // Rear right corner
 {-1.000, -0.900, 0.100, 1.500 * M_PI}, // Rear right side
};
static inline float sonarMetersFromBits(uint8_t bits) {
  return bits ? ((float)bits * 0.15) + 0.15 : 0.0;
}
static inline void sonarBuildPointCloud2(sensor_msgs::PointCloud2 &cloud, const dbw_mkz_msgs::SurroundReport &surround) {
  // Populate message fields
  const uint32_t POINT_STEP = 16;
  cloud.header.frame_id = "base_link";
  cloud.header.stamp = surround.header.stamp;
  cloud.fields.resize(4);
  cloud.fields[0].name = "x";
  cloud.fields[0].offset = 0;
  cloud.fields[0].datatype = sensor_msgs::PointField::FLOAT32;
  cloud.fields[0].count = 1;
  cloud.fields[1].name = "y";
  cloud.fields[1].offset = 4;
  cloud.fields[1].datatype = sensor_msgs::PointField::FLOAT32;
  cloud.fields[1].count = 1;
  cloud.fields[2].name = "z";
  cloud.fields[2].offset = 8;
  cloud.fields[2].datatype = sensor_msgs::PointField::FLOAT32;
  cloud.fields[2].count = 1;
  cloud.fields[3].name = "rgba";
  cloud.fields[3].offset = 12;
  cloud.fields[3].datatype = sensor_msgs::PointField::FLOAT32;
  cloud.fields[3].count = 1;
  cloud.data.resize(12 * POINT_STEP);

  uint8_t *ptr = cloud.data.data();
  for (unsigned int i = 0; i < 12; i++) {
    const float range = surround.sonar[i];
    if (range > 0.0) {
      *((float*)(ptr + 0)) = SONAR_TABLE[i].x + cosf(SONAR_TABLE[i].a) * range; // x
      *((float*)(ptr + 4)) = SONAR_TABLE[i].y + sinf(SONAR_TABLE[i].a) * range; // y
      *((float*)(ptr + 8)) = SONAR_TABLE[i].z; // z
      if (range < 0.7) {
        *((uint32_t*)(ptr + 12)) = 0xC0FF0000; // rgba = RED
      } else if (range < 1.3) {
        *((uint32_t*)(ptr + 12)) = 0xC0FFFF00; // rgba = YELLOW
      } else {
        *((uint32_t*)(ptr + 12)) = 0xC000FF00; // rgba = GREEN
      }
      ptr += POINT_STEP;
    }
  }
  if (ptr == cloud.data.data()) {
    // Prevent rviz from latching the last message
    *((float*)(ptr + 0)) = NAN; // x
    *((float*)(ptr + 4)) = NAN; // y
    *((float*)(ptr + 8)) = NAN; // z
    *((uint32_t*)(ptr + 12)) = 0x00000000; // rgba
    ptr += POINT_STEP;
  }

  // Populate message with number of valid points
  cloud.point_step = POINT_STEP;
  cloud.row_step = ptr - cloud.data.data();
  cloud.height = 1;
  cloud.width = cloud.row_step / POINT_STEP;
  cloud.is_bigendian = false;
  cloud.is_dense = true;
  cloud.data.resize(cloud.row_step); // Shrink to actual size
}

DbwNode::DbwNode(ros::NodeHandle &node, ros::NodeHandle &priv_nh)
: sync_imu_(10, boost::bind(&DbwNode::recvCanImu, this, _1), ID_REPORT_ACCEL, ID_REPORT_GYRO)
, sync_gps_(10, boost::bind(&DbwNode::recvCanGps, this, _1), ID_REPORT_GPS1, ID_REPORT_GPS2, ID_REPORT_GPS3)
{
  // Reduce synchronization delay
  sync_imu_.setInterMessageLowerBound(0, ros::Duration(0.003)); // 10ms period
  sync_imu_.setInterMessageLowerBound(1, ros::Duration(0.003)); // 10ms period
  sync_gps_.setInterMessageLowerBound(0, ros::Duration(0.3)); // 1s period
  sync_gps_.setInterMessageLowerBound(1, ros::Duration(0.3)); // 1s period
  sync_gps_.setInterMessageLowerBound(2, ros::Duration(0.3)); // 1s period

  // Initialize enable state machine
  prev_enable_ = true;
  enable_ = false;
  override_brake_ = false;
  override_throttle_ = false;
  override_steering_ = false;
  override_gear_ = false;
  fault_brakes_ = false;
  fault_throttle_ = false;
  fault_steering_ = false;
  fault_steering_cal_ = false;
  fault_watchdog_ = false;
  fault_watchdog_using_brakes_ = false;
  fault_watchdog_warned_ = false;

  // Setup brake lights (BOO)
  boo_status_ = false;
  boo_control_ = true;
  boo_thresh_lo_ = 0.20;
  boo_thresh_hi_ = 0.22;
  priv_nh.getParam("boo_control", boo_control_);
  priv_nh.getParam("boo_thresh_lo", boo_thresh_lo_);
  priv_nh.getParam("boo_thresh_hi", boo_thresh_hi_);
  if (boo_thresh_lo_ > boo_thresh_hi_) {
    std::swap(boo_thresh_lo_, boo_thresh_hi_);
  }

  // Ackermann steering parameters
  acker_wheelbase_ = 2.8498;
  acker_track_ = 1.6002;
  steering_ratio_ = 16.0;
  priv_nh.getParam("ackermann_wheelbase", acker_wheelbase_);
  priv_nh.getParam("ackermann_track", acker_track_);
  priv_nh.getParam("steering_ratio", steering_ratio_);

  // Initialize joint states
  joint_state_.position.resize(JOINT_COUNT);
  joint_state_.velocity.resize(JOINT_COUNT);
  joint_state_.effort.resize(JOINT_COUNT);
  joint_state_.name.resize(JOINT_COUNT);
  joint_state_.name[JOINT_FL] = "wheel_fl"; // Front Left
  joint_state_.name[JOINT_FR] = "wheel_fr"; // Front Right
  joint_state_.name[JOINT_RL] = "wheel_rl"; // Rear Left
  joint_state_.name[JOINT_RR] = "wheel_rr"; // Rear Right
  joint_state_.name[JOINT_SL] = "steer_fl";
  joint_state_.name[JOINT_SR] = "steer_fr";

  // Set up Publishers
  pub_can_ = node.advertise<dataspeed_can_msgs::CanMessage>("can_tx", 10);
  pub_brake_ = node.advertise<dbw_mkz_msgs::BrakeReport>("brake_report", 2);
  pub_throttle_ = node.advertise<dbw_mkz_msgs::ThrottleReport>("throttle_report", 2);
  pub_steering_ = node.advertise<dbw_mkz_msgs::SteeringReport>("steering_report", 2);
  pub_gear_ = node.advertise<dbw_mkz_msgs::GearReport>("gear_report", 2);
  pub_misc_1_ = node.advertise<dbw_mkz_msgs::Misc1Report>("misc_1_report", 2);
  pub_wheel_speeds_ = node.advertise<dbw_mkz_msgs::WheelSpeedReport>("wheel_speed_report", 2);
  pub_suspension_ = node.advertise<dbw_mkz_msgs::SuspensionReport>("suspension_report", 2);
  pub_tire_pressure_ = node.advertise<dbw_mkz_msgs::TirePressureReport>("tire_pressure_report", 2);
  pub_fuel_level_ = node.advertise<dbw_mkz_msgs::FuelLevelReport>("fuel_level_report", 2);
  pub_surround_ = node.advertise<dbw_mkz_msgs::SurroundReport>("surround_report", 2);
  pub_sonar_cloud_ = node.advertise<sensor_msgs::PointCloud2>("sonar_cloud", 2);
  pub_brake_info_ = node.advertise<dbw_mkz_msgs::BrakeInfoReport>("brake_info_report", 2);
  pub_throttle_info_ = node.advertise<dbw_mkz_msgs::ThrottleInfoReport>("throttle_info_report", 2);
  pub_imu_ = node.advertise<sensor_msgs::Imu>("imu/data_raw", 10);
  pub_gps_fix_ = node.advertise<sensor_msgs::NavSatFix>("gps/fix", 10);
  pub_gps_vel_ = node.advertise<geometry_msgs::TwistStamped>("gps/vel", 10);
  pub_gps_time_ = node.advertise<sensor_msgs::TimeReference>("gps/time", 10);
  pub_joint_states_ = node.advertise<sensor_msgs::JointState>("joint_states", 10, false);
  pub_twist_ = node.advertise<geometry_msgs::TwistStamped>("twist", 10);
  pub_sys_enable_ = node.advertise<std_msgs::Bool>("dbw_enabled", 1, true);
  publishDbwEnabled();

  // Set up Subscribers
  sub_enable_ = node.subscribe("enable", 10, &DbwNode::recvEnable, this, ros::TransportHints().tcpNoDelay(true));
  sub_disable_ = node.subscribe("disable", 10, &DbwNode::recvDisable, this, ros::TransportHints().tcpNoDelay(true));
  sub_can_ = node.subscribe("can_rx", 100, &DbwNode::recvCAN, this, ros::TransportHints().tcpNoDelay(true));
  sub_brake_ = node.subscribe("brake_cmd", 1, &DbwNode::recvBrakeCmd, this, ros::TransportHints().tcpNoDelay(true));
  sub_throttle_ = node.subscribe("throttle_cmd", 1, &DbwNode::recvThrottleCmd, this, ros::TransportHints().tcpNoDelay(true));
  sub_steering_ = node.subscribe("steering_cmd", 1, &DbwNode::recvSteeringCmd, this, ros::TransportHints().tcpNoDelay(true));
  sub_gear_ = node.subscribe("gear_cmd", 1, &DbwNode::recvGearCmd, this, ros::TransportHints().tcpNoDelay(true));
  sub_turn_signal_ = node.subscribe("turn_signal_cmd", 1, &DbwNode::recvTurnSignalCmd, this, ros::TransportHints().tcpNoDelay(true));

  // Set up Timer
  timer_ = node.createTimer(ros::Duration(1 / 20.0), &DbwNode::timerCallback, this);
}

DbwNode::~DbwNode()
{
}

void DbwNode::recvEnable(const std_msgs::Empty::ConstPtr& msg)
{
  enableSystem();
}

void DbwNode::recvDisable(const std_msgs::Empty::ConstPtr& msg)
{
  disableSystem();
}

void DbwNode::recvCAN(const dataspeed_can_msgs::CanMessageStamped::ConstPtr& msg)
{
  sync_imu_.processMsg(msg);
  sync_gps_.processMsg(msg);
  if (!msg->msg.extended) {
    switch (msg->msg.id) {
      case ID_BRAKE_REPORT:
        if (msg->msg.dlc >= sizeof(MsgBrakeReport)) {
          const MsgBrakeReport *ptr = (const MsgBrakeReport*)msg->msg.data.elems;
          faultBrakes(ptr->FLT1 && ptr->FLT2);
          faultWatchdog(ptr->FLTWDC, ptr->WDCSRC, ptr->WDCBRK);
          overrideBrake(ptr->OVERRIDE);
          dbw_mkz_msgs::BrakeReport out;
          out.header.stamp = msg->header.stamp;
          out.pedal_input  = (float)ptr->PI / UINT16_MAX;
          out.pedal_cmd    = (float)ptr->PC / UINT16_MAX;
          out.pedal_output = (float)ptr->PO / UINT16_MAX;
          out.torque_input = brakeTorqueFromPedal(out.pedal_input);
          out.torque_cmd = brakeTorqueFromPedal(out.pedal_cmd);
          out.torque_output = brakeTorqueFromPedal(out.pedal_output);
          out.boo_input  = ptr->BI ? true : false;
          out.boo_cmd    = ptr->BC ? true : false;
          out.boo_output = ptr->BO ? true : false;
          out.enabled = ptr->ENABLED ? true : false;
          out.override = ptr->OVERRIDE ? true : false;
          out.driver = ptr->DRIVER ? true : false;
          out.watchdog_counter.source = ptr->WDCSRC;
          out.watchdog_braking = ptr->WDCBRK ? true : false;
          out.fault_wdc = ptr->FLTWDC ? true : false;
          out.fault_ch1 = ptr->FLT1 ? true : false;
          out.fault_ch2 = ptr->FLT2 ? true : false;
          out.fault_boo = ptr->FLTB ? true : false;
          out.fault_connector = ptr->FLTCON ? true : false;
          pub_brake_.publish(out);
          if (ptr->FLT1 || ptr->FLT2) {
            ROS_WARN_THROTTLE(5.0, "Brake pedal fault. Check brake pedal wiring.");
          }
        }
        break;

      case ID_THROTTLE_REPORT:
        if (msg->msg.dlc >= sizeof(MsgThrottleReport)) {
          const MsgThrottleReport *ptr = (const MsgThrottleReport*)msg->msg.data.elems;
          faultThrottle(ptr->FLT1 && ptr->FLT2);
          faultWatchdog(ptr->FLTWDC, ptr->WDCSRC);
          overrideThrottle(ptr->OVERRIDE);
          dbw_mkz_msgs::ThrottleReport out;
          out.header.stamp = msg->header.stamp;
          out.pedal_input  = (float)ptr->PI / UINT16_MAX;
          out.pedal_cmd    = (float)ptr->PC / UINT16_MAX;
          out.pedal_output = (float)ptr->PO / UINT16_MAX;
          out.enabled = ptr->ENABLED ? true : false;
          out.override = ptr->OVERRIDE ? true : false;
          out.driver = ptr->DRIVER ? true : false;
          out.watchdog_counter.source = ptr->WDCSRC;
          out.fault_wdc = ptr->FLTWDC ? true : false;
          out.fault_ch1 = ptr->FLT1 ? true : false;
          out.fault_ch2 = ptr->FLT2 ? true : false;
          out.fault_connector = ptr->FLTCON ? true : false;
          pub_throttle_.publish(out);
          if (ptr->FLT1 || ptr->FLT2) {
            ROS_WARN_THROTTLE(5.0, "Throttle pedal fault. Check throttle pedal wiring.");
          }
        }
        break;

      case ID_STEERING_REPORT:
        ROS_INFO("DbwNode::recvCAN, Case ID_STEERING_REPORT detected = %i", ID_STEERING_REPORT);
        if (msg->msg.dlc >= sizeof(MsgSteeringReport)) {
          const MsgSteeringReport *ptr = (const MsgSteeringReport*)msg->msg.data.elems;
          faultSteering(ptr->FLTBUS1 && ptr->FLTBUS2);
          faultSteeringCal(ptr->FLTCAL);
          faultWatchdog(ptr->FLTWDC);
          overrideSteering(ptr->OVERRIDE);
          dbw_mkz_msgs::SteeringReport out;
          out.header.stamp = msg->header.stamp;
          out.steering_wheel_angle     = (float)ptr->ANGLE * (0.1 * M_PI / 180);
          out.steering_wheel_angle_cmd = (float)ptr->CMD   * (0.1 * M_PI / 180);
          out.steering_wheel_torque = (float)ptr->TORQUE * 0.0625;
          out.speed = (float)ptr->SPEED * (0.01 / 3.6);
          out.enabled = ptr->ENABLED ? true : false;
          out.override = ptr->OVERRIDE ? true : false;
          out.driver = ptr->DRIVER ? true : false;
          out.fault_wdc = ptr->FLTWDC ? true : false;
          out.fault_bus1 = ptr->FLTBUS1 ? true : false;
          out.fault_bus2 = ptr->FLTBUS2 ? true : false;
          out.fault_calibration = ptr->FLTCAL ? true : false;
          out.fault_connector = ptr->FLTCON ? true : false;
          pub_steering_.publish(out);
          geometry_msgs::TwistStamped twist;
          twist.header.stamp = out.header.stamp;
          twist.twist.linear.x = out.speed;
          twist.twist.angular.z = out.speed * tan(out.steering_wheel_angle / steering_ratio_) / acker_wheelbase_;
          pub_twist_.publish(twist);
          publishJointStates(msg->header.stamp, NULL, &out);
          if (ptr->FLTBUS1 || ptr->FLTBUS2) {
            ROS_WARN_THROTTLE(5.0, "Steering fault. Check wiring.");
          } else if (ptr->FLTCAL) {
            ROS_WARN_THROTTLE(5.0, "Steering calibration fault. Drive at least 25 mph for at least 10 seconds in a straight line.");
          }
        }
        break;

      case ID_GEAR_REPORT:
        if (msg->msg.dlc >= sizeof(MsgGearReport)) {
          const MsgGearReport *ptr = (const MsgGearReport*)msg->msg.data.elems;
          overrideGear(ptr->OVERRIDE);
          dbw_mkz_msgs::GearReport out;
          out.header.stamp = msg->header.stamp;
          out.state.gear = ptr->STATE;
          out.cmd.gear = ptr->CMD;
          out.override = ptr->OVERRIDE ? true : false;
          out.fault_bus = ptr->FLTBUS ? true : false;
          pub_gear_.publish(out);
        }
        break;

      case ID_MISC_REPORT:
        if (msg->msg.dlc >= 3) {
          const MsgMiscReport *ptr = (const MsgMiscReport*)msg->msg.data.elems;
          if (ptr->btn_cc_gap_inc || ptr->btn_cc_cncl) {
            buttonCancel();
          } else if ((ptr->btn_cc_set_dec && ptr->btn_cc_gap_dec) || (ptr->btn_cc_set_inc && ptr->btn_cc_off)) {
            enableSystem();
          }
          dbw_mkz_msgs::Misc1Report out;
          out.header.stamp = msg->header.stamp;
          out.turn_signal.value = ptr->turn_signal;
          out.high_beam_headlights = ptr->head_light_hi ? true : false;
          out.wiper.status = ptr->wiper_front;
          out.ambient_light.status = ptr->light_ambient;
          out.btn_cc_on = ptr->btn_cc_on ? true : false;
          out.btn_cc_off = ptr->btn_cc_off ? true : false;
          out.btn_cc_on_off = ptr->btn_cc_on_off ? true : false;
          out.btn_cc_res = ptr->btn_cc_res ? true : false;
          out.btn_cc_cncl = ptr->btn_cc_cncl ? true : false;
          out.btn_cc_res_cncl = ptr->btn_cc_res_cncl ? true : false;
          out.btn_cc_set_inc = ptr->btn_cc_set_inc ? true : false;
          out.btn_cc_set_dec = ptr->btn_cc_set_dec ? true : false;
          out.btn_cc_gap_inc = ptr->btn_cc_gap_inc ? true : false;
          out.btn_cc_gap_dec = ptr->btn_cc_gap_dec ? true : false;
          out.btn_la_on_off = ptr->btn_la_on_off ? true : false;
          out.fault_bus = ptr->FLTBUS ? true : false;
          if (msg->msg.dlc >= sizeof(MsgMiscReport)) {
            out.door_driver = ptr->door_driver ? true : false;
            out.door_passenger = ptr->door_passenger ? true : false;
            out.door_rear_left = ptr->door_rear_left ? true : false;
            out.door_rear_right = ptr->door_rear_right ? true : false;
            out.door_hood = ptr->door_hood ? true : false;
            out.door_trunk = ptr->door_trunk ? true : false;
            out.passenger_detect = ptr->pasngr_detect ? true : false;
            out.passenger_airbag = ptr->pasngr_airbag ? true : false;
            out.buckle_driver = ptr->buckle_driver ? true : false;
            out.buckle_passenger = ptr->buckle_pasngr ? true : false;
          }
          pub_misc_1_.publish(out);
        }
        break;

      case ID_REPORT_WHEEL_SPEED:
        if (msg->msg.dlc >= sizeof(MsgReportWheelSpeed)) {
          const MsgReportWheelSpeed *ptr = (const MsgReportWheelSpeed*)msg->msg.data.elems;
          dbw_mkz_msgs::WheelSpeedReport out;
          out.header.stamp = msg->header.stamp;
          out.front_left  = (float)ptr->front_left  * 0.01;
          out.front_right = (float)ptr->front_right * 0.01;
          out.rear_left   = (float)ptr->rear_left   * 0.01;
          out.rear_right  = (float)ptr->rear_right  * 0.01;
          pub_wheel_speeds_.publish(out);
          publishJointStates(msg->header.stamp, &out, NULL);
        }
        break;

      case ID_REPORT_SUSPENSION:
        if (msg->msg.dlc >= sizeof(MsgReportSuspension)) {
          const MsgReportSuspension *ptr = (const MsgReportSuspension*)msg->msg.data.elems;
          dbw_mkz_msgs::SuspensionReport out;
          out.header.stamp = msg->header.stamp;
          out.front_left  = (float)ptr->front_left  * 0.3913895e-3;
          out.front_right = (float)ptr->front_right * 0.3913895e-3;
          out.rear_left   = (float)ptr->rear_left   * 0.3913895e-3;
          out.rear_right  = (float)ptr->rear_right  * 0.3913895e-3;
          pub_suspension_.publish(out);
        }
        break;

      case ID_REPORT_TIRE_PRESSURE:
        if (msg->msg.dlc >= sizeof(MsgReportTirePressure)) {
          const MsgReportTirePressure *ptr = (const MsgReportTirePressure*)msg->msg.data.elems;
          dbw_mkz_msgs::TirePressureReport out;
          out.header.stamp = msg->header.stamp;
          out.front_left  = (float)ptr->front_left;
          out.front_right = (float)ptr->front_right;
          out.rear_left   = (float)ptr->rear_left;
          out.rear_right  = (float)ptr->rear_right;
          pub_tire_pressure_.publish(out);
        }
        break;

      case ID_REPORT_FUEL_LEVEL:
        if (msg->msg.dlc >= sizeof(MsgReportFuelLevel)) {
          const MsgReportFuelLevel *ptr = (const MsgReportFuelLevel*)msg->msg.data.elems;
          dbw_mkz_msgs::FuelLevelReport out;
          out.header.stamp = msg->header.stamp;
          out.fuel_level  = (float)ptr->fuel_level * 0.108696;
          pub_fuel_level_.publish(out);
        }
        break;

      case ID_REPORT_SURROUND:
        if (msg->msg.dlc >= sizeof(MsgReportSurround)) {
          const MsgReportSurround *ptr = (const MsgReportSurround*)msg->msg.data.elems;
          dbw_mkz_msgs::SurroundReport out;
          out.header.stamp = msg->header.stamp;
          out.cta_left_alert = ptr->l_cta_alert ? true : false;
          out.cta_right_alert = ptr->r_cta_alert ? true : false;
          out.cta_left_enabled = ptr->l_cta_enabled ? true : false;
          out.cta_right_enabled = ptr->r_cta_enabled ? true : false;
          out.blis_left_alert = ptr->l_blis_alert ? true : false;
          out.blis_right_alert = ptr->r_blis_alert ? true : false;
          out.blis_left_enabled = ptr->l_blis_enabled ? true : false;
          out.blis_right_enabled = ptr->r_blis_enabled ? true : false;
          out.sonar_enabled = ptr->sonar_enabled ? true : false;
          out.sonar_fault = ptr->sonar_fault ? true : false;
          if (out.sonar_enabled) {
            out.sonar[0] = sonarMetersFromBits(ptr->sonar_00);
            out.sonar[1] = sonarMetersFromBits(ptr->sonar_01);
            out.sonar[2] = sonarMetersFromBits(ptr->sonar_02);
            out.sonar[3] = sonarMetersFromBits(ptr->sonar_03);
            out.sonar[4] = sonarMetersFromBits(ptr->sonar_04);
            out.sonar[5] = sonarMetersFromBits(ptr->sonar_05);
            out.sonar[6] = sonarMetersFromBits(ptr->sonar_06);
            out.sonar[7] = sonarMetersFromBits(ptr->sonar_07);
            out.sonar[8] = sonarMetersFromBits(ptr->sonar_08);
            out.sonar[9] = sonarMetersFromBits(ptr->sonar_09);
            out.sonar[10] = sonarMetersFromBits(ptr->sonar_10);
            out.sonar[11] = sonarMetersFromBits(ptr->sonar_11);
          }
          pub_surround_.publish(out);
          sensor_msgs::PointCloud2 cloud;
          sonarBuildPointCloud2(cloud, out);
          pub_sonar_cloud_.publish(cloud);
        }
        break;

      case ID_REPORT_BRAKE_INFO:
        if (msg->msg.dlc >= sizeof(MsgReportBrakeInfo)) {
          const MsgReportBrakeInfo *ptr = (const MsgReportBrakeInfo*)msg->msg.data.elems;
          dbw_mkz_msgs::BrakeInfoReport out;
          out.header.stamp = msg->header.stamp;
          out.brake_torque_request = (float)ptr->brake_torque_request * 4.0;
          out.brake_torque_actual = (float)ptr->brake_torque_actual * 4.0;
          out.wheel_torque_actual = (float)ptr->wheel_torque * 4.0;
          out.accel_over_ground = (float)ptr->accel_over_ground_est * 0.035;
          out.hsa.status = ptr->hsa_stat;
          out.hsa.mode = ptr->hsa_mode;
          out.abs_active = ptr->abs_active ? true : false;
          out.abs_enabled = ptr->abs_enabled ? true : false;
          out.stab_active = ptr->stab_active ? true : false;
          out.stab_enabled = ptr->stab_enabled ? true : false;
          out.trac_active = ptr->trac_active ? true : false;
          out.trac_enabled = ptr->trac_enabled ? true : false;
          out.parking_brake.status = ptr->parking_brake;
          out.stationary = ptr->stationary;
          pub_brake_info_.publish(out);
        }
        break;

      case ID_REPORT_THROTTLE_INFO:
        if (msg->msg.dlc >= sizeof(MsgReportThrottleInfo)) {
          const MsgReportThrottleInfo *ptr = (const MsgReportThrottleInfo*)msg->msg.data.elems;
          dbw_mkz_msgs::ThrottleInfoReport out;
          out.header.stamp = msg->header.stamp;
          out.throttle_pc = (float)ptr->throttle_pc * 1e-3;
          out.throttle_rate = (float)ptr->throttle_rate * 4e-4;
          out.engine_rpm = (float)ptr->engine_rpm * 0.25;
          pub_throttle_info_.publish(out);
        }
        break;

      case ID_VERSION:
        if (msg->msg.dlc >= sizeof(MsgVersion)) {
          const MsgVersion *ptr = (const MsgVersion*)msg->msg.data.elems;
          if (ptr->module == VERSION_BPEC) {
            ROS_INFO_ONCE("Detected brake firmware version %u.%u.%u", ptr->major, ptr->minor, ptr->build);
          } else if (ptr->module == VERSION_TPEC) {
            ROS_INFO_ONCE("Detected throttle firmware version %u.%u.%u", ptr->major, ptr->minor, ptr->build);
          } else if (ptr->module == VERSION_EPAS) {
            ROS_INFO_ONCE("Detected steering firmware version %u.%u.%u", ptr->major, ptr->minor, ptr->build);
          } else {
            ROS_WARN_THROTTLE(10.0, "Detected unknown firmware version %u.%u.%u", ptr->major, ptr->minor, ptr->build);
          }
        }
        break;

      case ID_BRAKE_CMD:
        ROS_WARN("DBW system: Another node on the CAN bus is commanding the vehicle!!! Subsystem: Brake. Id: 0x%03X", ID_BRAKE_CMD);
        break;
      case ID_THROTTLE_CMD:
        ROS_WARN("DBW system: Another node on the CAN bus is commanding the vehicle!!! Subsystem: Throttle. Id: 0x%03X", ID_THROTTLE_CMD);
        break;
      case ID_STEERING_CMD:
        ROS_WARN("DBW system: Another node on the CAN bus is commanding the vehicle!!! Subsystem: Steering. Id: 0x%03X", ID_STEERING_CMD);
        break;
      case ID_GEAR_CMD:
        ROS_WARN("DBW system: Another node on the CAN bus is commanding the vehicle!!! Subsystem: Shifting. Id: 0x%03X", ID_GEAR_CMD);
        break;
      case ID_MISC_CMD:
        ROS_WARN("DBW system: Another node on the CAN bus is commanding the vehicle!!! Subsystem: Turn Signals. Id: 0x%03X", ID_MISC_CMD);
        break;
    }
  }
#if 0
  ROS_INFO("ena: %s, clr: %s, brake: %s, throttle: %s, steering: %s, gear: %s",
           enabled() ? "true " : "false",
           clear() ? "true " : "false",
           override_brake_ ? "true " : "false",
           override_throttle_ ? "true " : "false",
           override_steering_ ? "true " : "false",
           override_gear_ ? "true " : "false"
       );
#endif
}

void DbwNode::recvCanImu(const std::vector<dataspeed_can_msgs::CanMessageStamped::ConstPtr> &msgs) {
  ROS_ASSERT(msgs.size() == 2);
  ROS_ASSERT(msgs[0]->msg.id == ID_REPORT_ACCEL);
  ROS_ASSERT(msgs[1]->msg.id == ID_REPORT_GYRO);
  if ((msgs[0]->msg.dlc >= sizeof(MsgReportAccel)) && (msgs[1]->msg.dlc >= sizeof(MsgReportGyro))) {
    const MsgReportAccel *ptr_accel = (const MsgReportAccel*)msgs[0]->msg.data.elems;
    const MsgReportGyro *ptr_gyro = (const MsgReportGyro*)msgs[1]->msg.data.elems;
    sensor_msgs::Imu out;
    out.header.stamp = msgs[0]->header.stamp;
    out.linear_acceleration.x = (double)ptr_accel->accel_lat * 0.01;
    out.linear_acceleration.y = (double)ptr_accel->accel_long * 0.01;
    out.linear_acceleration.z = (double)ptr_accel->accel_vert * 0.01;
    out.linear_acceleration_covariance[0] = -1;
    out.angular_velocity.x = (double)ptr_gyro->gyro_roll * 0.0002;
    out.angular_velocity.z = (double)ptr_gyro->gyro_yaw * 0.0002;
    out.angular_velocity_covariance[0] = -1;
    pub_imu_.publish(out);
  }
#if 0
  ROS_INFO("Time: %u.%u, %u.%u, delta: %fms",
           msgs[0]->header.stamp.sec, msgs[0]->header.stamp.nsec,
           msgs[1]->header.stamp.sec, msgs[1]->header.stamp.nsec,
           labs((msgs[1]->header.stamp - msgs[0]->header.stamp).toNSec()) / 1000000.0);
#endif
}

void DbwNode::recvCanGps(const std::vector<dataspeed_can_msgs::CanMessageStamped::ConstPtr> &msgs) {
  ROS_ASSERT(msgs.size() == 3);
  ROS_ASSERT(msgs[0]->msg.id == ID_REPORT_GPS1);
  ROS_ASSERT(msgs[1]->msg.id == ID_REPORT_GPS2);
  ROS_ASSERT(msgs[2]->msg.id == ID_REPORT_GPS3);
  if ((msgs[0]->msg.dlc >= sizeof(MsgReportGps1)) && (msgs[1]->msg.dlc >= sizeof(MsgReportGps2)) && (msgs[2]->msg.dlc >= sizeof(MsgReportGps3))) {
    const MsgReportGps1 *ptr1 = (const MsgReportGps1*)msgs[0]->msg.data.elems;
    const MsgReportGps2 *ptr2 = (const MsgReportGps2*)msgs[1]->msg.data.elems;
    const MsgReportGps3 *ptr3 = (const MsgReportGps3*)msgs[2]->msg.data.elems;

    sensor_msgs::NavSatFix msg_fix;
    msg_fix.header.stamp =  msgs[0]->header.stamp;
    msg_fix.latitude = (double)ptr1->latitude / 3e6;
    msg_fix.longitude = (double)ptr1->longitude / 3e6;
    msg_fix.altitude = (double)ptr3->altitude * 0.25;
    msg_fix.position_covariance_type = sensor_msgs::NavSatFix::COVARIANCE_TYPE_UNKNOWN;
    msg_fix.status.service = sensor_msgs::NavSatStatus::SERVICE_GPS;
    switch (ptr3->quality) {
      case 0:
      default:
        msg_fix.status.status = sensor_msgs::NavSatStatus::STATUS_NO_FIX;
        break;
      case 1:
      case 2:
        msg_fix.status.status = sensor_msgs::NavSatStatus::STATUS_FIX;
        break;
    }
    pub_gps_fix_.publish(msg_fix);

    geometry_msgs::TwistStamped msg_vel;
    msg_vel.header.stamp = msgs[0]->header.stamp;
    double heading = (double)ptr3->heading * (0.01 * M_PI / 180);
    double speed = (double)ptr3->speed * 0.44704;
    msg_vel.twist.linear.x = cos(heading) * speed;
    msg_vel.twist.linear.y = sin(heading) * speed;
    pub_gps_vel_.publish(msg_vel);

    sensor_msgs::TimeReference msg_time;
    struct tm unix_time;
    unix_time.tm_year = ptr2->utc_year + 100; // [1900] <-- [2000]
    unix_time.tm_mon = ptr2->utc_month - 1;   // [0-11] <-- [1-12]
    unix_time.tm_mday = ptr2->utc_day;        // [1-31] <-- [1-31]
    unix_time.tm_hour = ptr2->utc_hours;      // [0-23] <-- [0-23]
    unix_time.tm_min = ptr2->utc_minutes;     // [0-59] <-- [0-59]
    unix_time.tm_sec = ptr2->utc_seconds;     // [0-59] <-- [0-59]
    msg_time.header.stamp = msgs[0]->header.stamp;
    msg_time.time_ref.sec = timegm(&unix_time);
    msg_time.time_ref.nsec = 0;
    pub_gps_time_.publish(msg_time);

#if 0
    ROS_INFO("UTC Time: %04d-%02d-%02d %02d:%02d:%02d",
             2000 + ptr2->utc_year, ptr2->utc_month, ptr2->utc_day,
             ptr2->utc_hours, ptr2->utc_minutes, ptr2->utc_seconds);
#endif
  }
#if 0
  ROS_INFO("Time: %u.%u, %u.%u, %u.%u, delta: %fms",
           msgs[0]->header.stamp.sec, msgs[0]->header.stamp.nsec,
           msgs[1]->header.stamp.sec, msgs[1]->header.stamp.nsec,
           msgs[2]->header.stamp.sec, msgs[2]->header.stamp.nsec,
           std::max(std::max(
               labs((msgs[1]->header.stamp - msgs[0]->header.stamp).toNSec()),
               labs((msgs[2]->header.stamp - msgs[1]->header.stamp).toNSec())),
               labs((msgs[0]->header.stamp - msgs[2]->header.stamp).toNSec())) / 1000000.0);
#endif
}

void DbwNode::recvBrakeCmd(const dbw_mkz_msgs::BrakeCmd::ConstPtr& msg)
{
  dataspeed_can_msgs::CanMessage out;
  out.id = ID_BRAKE_CMD;
  out.extended = false;
  out.dlc = sizeof(MsgBrakeCmd);
  MsgBrakeCmd *ptr = (MsgBrakeCmd*)out.data.elems;
  memset(ptr, 0x00, sizeof(*ptr));
  if (enabled()) {
    float cmd = 0.0;
    switch (msg->pedal_cmd_type) {
      default:
      case dbw_mkz_msgs::BrakeCmd::CMD_NONE:
        break;
      case dbw_mkz_msgs::BrakeCmd::CMD_PEDAL:
        cmd = msg->pedal_cmd;
        break;
      case dbw_mkz_msgs::BrakeCmd::CMD_PERCENT:
        cmd = brakePedalFromPercent(msg->pedal_cmd);
        break;
      case dbw_mkz_msgs::BrakeCmd::CMD_TORQUE:
        cmd = brakePedalFromTorque(msg->pedal_cmd);
        break;
    }
    ptr->PCMD = std::max((float)0.0, std::min((float)UINT16_MAX, cmd * UINT16_MAX));
    if (msg->boo_cmd) {
      ptr->BCMD = 1;
      boo_status_ = true;
    } else if (boo_control_) {
      if (boo_status_) {
        ptr->BCMD = 1;
      }
      if (!boo_status_ && (cmd > boo_thresh_hi_)) {
        ptr->BCMD = 1;
        boo_status_ = true;
      } else if (boo_status_ && (cmd < boo_thresh_lo_)) {
        ptr->BCMD = 0;
        boo_status_ = false;
      }
    }
    if (msg->enable) {
      ptr->EN = 1;
    }
  }
  if (clear()) {
    ptr->CLEAR = 1;
  }
  if (msg->ignore) {
    ptr->IGNORE = 1;
  }
  ptr->count = msg->count;
  pub_can_.publish(out);
}

void DbwNode::recvThrottleCmd(const dbw_mkz_msgs::ThrottleCmd::ConstPtr& msg)
{
  dataspeed_can_msgs::CanMessage out;
  out.id = ID_THROTTLE_CMD;
  out.extended = false;
  out.dlc = sizeof(MsgThrottleCmd);
  MsgThrottleCmd *ptr = (MsgThrottleCmd*)out.data.elems;
  memset(ptr, 0x00, sizeof(*ptr));
  if (enabled()) {
    float cmd = 0.0;
    switch (msg->pedal_cmd_type) {
      default:
      case dbw_mkz_msgs::ThrottleCmd::CMD_NONE:
        break;
      case dbw_mkz_msgs::ThrottleCmd::CMD_PEDAL:
        cmd = msg->pedal_cmd;
        break;
      case dbw_mkz_msgs::ThrottleCmd::CMD_PERCENT:
        cmd = throttlePedalFromPercent(msg->pedal_cmd);
        break;
    }
    ptr->PCMD = std::max((float)0.0, std::min((float)UINT16_MAX, cmd * UINT16_MAX));
    if (msg->enable) {
      ptr->EN = 1;
    }
  }
  if (clear()) {
    ptr->CLEAR = 1;
  }
  if (msg->ignore) {
    ptr->IGNORE = 1;
  }
  ptr->count = msg->count;
  pub_can_.publish(out);
}

void DbwNode::recvSteeringCmd(const dbw_mkz_msgs::SteeringCmd::ConstPtr& msg)
{
  dataspeed_can_msgs::CanMessage out;
  out.id = ID_STEERING_CMD;
  out.extended = false;
  out.dlc = sizeof(MsgSteeringCmd);
  MsgSteeringCmd *ptr = (MsgSteeringCmd*)out.data.elems;
  memset(ptr, 0x00, sizeof(*ptr));
  if (enabled()) {
    ptr->SCMD = std::max((float)-4700, std::min((float)4700, (float)(msg->steering_wheel_angle_cmd * (180 / M_PI * 10))));
    //ROS_INFO("msg->steering_wheel_angle_cmd radians=== %f", msg->steering_wheel_angle_cmd);
    //ROS_INFO("msg->steering_wheel_angle_cmd in degrees and multip 10=== %f", (msg->steering_wheel_angle_cmd * (180 / M_PI * 10)));
    //ROS_INFO("ptr->SCMD === %i", ptr->SCMD);
    if (fabsf(msg->steering_wheel_angle_velocity) > 0) {
      ptr->SVEL = std::max((float)1, std::min((float)254, (float)roundf(fabsf(msg->steering_wheel_angle_velocity) * 180 / M_PI / 2)));
    }
    if (msg->enable) {
      ptr->EN = 1;
    }
  }
  if (clear()) {
    ptr->CLEAR = 1;
  }
  if (msg->ignore) {
    ptr->IGNORE = 1;
  }
  if (msg->quiet) {
    ptr->QUIET = 1;
  }
  ptr->count = msg->count;
  pub_can_.publish(out);
}

void DbwNode::recvGearCmd(const dbw_mkz_msgs::GearCmd::ConstPtr& msg)
{
  dataspeed_can_msgs::CanMessage out;
  out.id = ID_GEAR_CMD;
  out.extended = false;
  out.dlc = sizeof(MsgGearCmd);
  MsgGearCmd *ptr = (MsgGearCmd*)out.data.elems;
  memset(ptr, 0x00, sizeof(*ptr));
  if (enabled()) {
    ptr->GCMD = msg->cmd.gear;
  }
  pub_can_.publish(out);
}

void DbwNode::recvTurnSignalCmd(const dbw_mkz_msgs::TurnSignalCmd::ConstPtr& msg)
{
  dataspeed_can_msgs::CanMessage out;
  out.id = ID_MISC_CMD;
  out.extended = false;
  out.dlc = sizeof(MsgTurnSignalCmd);
  MsgTurnSignalCmd *ptr = (MsgTurnSignalCmd*)out.data.elems;
  memset(ptr, 0x00, sizeof(*ptr));
  if (enabled()) {
    ptr->TRNCMD = msg->cmd.value;
  }
  pub_can_.publish(out);
}

bool DbwNode::publishDbwEnabled()
{
  bool change = false;
  bool en = enabled();
  if (prev_enable_ != en) {
    std_msgs::Bool msg;
    msg.data = en;
    pub_sys_enable_.publish(msg);
    change = true;
  }
  prev_enable_ = en;
  return change;
}

void DbwNode::timerCallback(const ros::TimerEvent& event)
{
  if (clear()) {
    dataspeed_can_msgs::CanMessage out;
    out.extended = false;

    if (override_brake_) {
      out.id = ID_BRAKE_CMD;
      out.dlc = 4; // Sending the full eight bytes will fault the watchdog counter (if enabled)
      memset(out.data.elems, 0x00, 8);
      ((MsgBrakeCmd*)out.data.elems)->CLEAR = 1;
      pub_can_.publish(out);
    }

    if (override_throttle_) {
      out.id = ID_THROTTLE_CMD;
      out.dlc = 4; // Sending the full eight bytes will fault the watchdog counter (if enabled)
      memset(out.data.elems, 0x00, 8);
      ((MsgThrottleCmd*)out.data.elems)->CLEAR = 1;
      pub_can_.publish(out);
    }

    if (override_steering_) {
      out.id = ID_STEERING_CMD;
      out.dlc = 4; // Sending the full eight bytes will fault the watchdog counter (if enabled)
      memset(out.data.elems, 0x00, 8);
      ((MsgSteeringCmd*)out.data.elems)->CLEAR = 1;
      pub_can_.publish(out);
    }

    if (override_gear_) {
      out.id = ID_GEAR_CMD;
      out.dlc = sizeof(MsgGearCmd);
      memset(out.data.elems, 0x00, 8);
      ((MsgGearCmd*)out.data.elems)->CLEAR = 1;
      pub_can_.publish(out);
    }
  }
}

void DbwNode::enableSystem()
{
  if (!enable_) {
    if (fault()) {
      if (fault_steering_cal_) {
        ROS_WARN("DBW system not enabled. Steering calibration fault.");
      }
      if (fault_brakes_) {
        ROS_WARN("DBW system not enabled. Braking fault.");
      }
      if (fault_throttle_) {
        ROS_WARN("DBW system not enabled. Throttle fault.");
      }
      if (fault_watchdog_) {
        ROS_WARN("DBW system not enabled. Watchdog fault.");
      }
    } else {
      enable_ = true;
      if (publishDbwEnabled()) {
        ROS_INFO("DBW system enabled.");
      } else {
        ROS_INFO("DBW system enable requested. Waiting for ready.");
      }
    }
  } else {
      ROS_INFO("The Enable Variable already exists");
  }
}

void DbwNode::disableSystem()
{
  if (enable_) {
    enable_ = false;
    publishDbwEnabled();
    ROS_WARN("DBW system disabled.");
  }
}

void DbwNode::buttonCancel()
{
  if (enable_) {
    enable_ = false;
    publishDbwEnabled();
    ROS_WARN("DBW system disabled. Cancel button pressed.");
  }
}

void DbwNode::overrideBrake(bool override)
{
  bool en = enabled();
  if (override && en) {
    enable_ = false;
  }
  override_brake_ = override;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_WARN("DBW system disabled. Driver override on brake/throttle pedal.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
}

void DbwNode::overrideThrottle(bool override)
{
  bool en = enabled();
  if (override && en) {
    enable_ = false;
  }
  override_throttle_ = override;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_WARN("DBW system disabled. Driver override on brake/throttle pedal.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
}

void DbwNode::overrideSteering(bool override)
{
  bool en = enabled();
  if (override && en) {
    enable_ = false;
  }
  override_steering_ = override;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_WARN("DBW system disabled. Driver override on steering wheel.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
}

void DbwNode::overrideGear(bool override)
{
  bool en = enabled();
  if (override && en) {
    enable_ = false;
  }
  override_gear_ = override;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_WARN("DBW system disabled. Driver override on shifter.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
}

void DbwNode::faultBrakes(bool fault)
{
  bool en = enabled();
  if (fault && en) {
    enable_ = false;
  }
  fault_brakes_ = fault;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_ERROR("DBW system disabled. Braking fault.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
}

void DbwNode::faultThrottle(bool fault)
{
  bool en = enabled();
  if (fault && en) {
    enable_ = false;
  }
  fault_throttle_ = fault;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_ERROR("DBW system disabled. Throttle fault.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
}

void DbwNode::faultSteering(bool fault)
{
  bool en = enabled();
  if (fault && en) {
    enable_ = false;
  }
  fault_steering_ = fault;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_ERROR("DBW system disabled. Steering fault.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
}

void DbwNode::faultSteeringCal(bool fault)
{
  bool en = enabled();
  if (fault && en) {
    enable_ = false;
  }
  fault_steering_cal_ = fault;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_ERROR("DBW system disabled. Steering calibration fault.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
}

void DbwNode::faultWatchdog(bool fault, uint8_t src, bool braking)
{
  bool en = enabled();
  if (fault && en) {
    enable_ = false;
  }
  fault_watchdog_ = fault;
  if (publishDbwEnabled()) {
    if (en) {
      ROS_ERROR("DBW system disabled. Watchdog fault.");
    } else {
      ROS_INFO("DBW system enabled.");
    }
  }
  if (braking && !fault_watchdog_using_brakes_) {
    ROS_WARN("Watchdog event: Alerting driver and applying brakes.");
  } else if (!braking && fault_watchdog_using_brakes_) {
    ROS_INFO("Watchdog event: Driver has successfully taken control.");
  }
  if (fault && src && !fault_watchdog_warned_) {
      switch (src) {
        case dbw_mkz_msgs::WatchdogCounter::OTHER_BRAKE:
          ROS_WARN("Watchdog event: Fault determined by brake controller");
          break;
        case dbw_mkz_msgs::WatchdogCounter::OTHER_THROTTLE:
          ROS_WARN("Watchdog event: Fault determined by throttle controller");
          break;
        case dbw_mkz_msgs::WatchdogCounter::OTHER_STEERING:
          ROS_WARN("Watchdog event: Fault determined by steering controller");
          break;
        case dbw_mkz_msgs::WatchdogCounter::BRAKE_COUNTER:
          ROS_WARN("Watchdog event: Brake command counter failed to increment");
          break;
        case dbw_mkz_msgs::WatchdogCounter::BRAKE_DISABLED:
          ROS_WARN("Watchdog event: Brake transition to disabled while in gear or moving");
          break;
        case dbw_mkz_msgs::WatchdogCounter::BRAKE_COMMAND:
          ROS_WARN("Watchdog event: Brake command timeout after 100ms");
          break;
        case dbw_mkz_msgs::WatchdogCounter::BRAKE_REPORT:
          ROS_WARN("Watchdog event: Brake report timeout after 100ms");
          break;
        case dbw_mkz_msgs::WatchdogCounter::THROTTLE_COUNTER:
          ROS_WARN("Watchdog event: Throttle command counter failed to increment");
          break;
        case dbw_mkz_msgs::WatchdogCounter::THROTTLE_DISABLED:
          ROS_WARN("Watchdog event: Throttle transition to disabled while in gear or moving");
          break;
        case dbw_mkz_msgs::WatchdogCounter::THROTTLE_COMMAND:
          ROS_WARN("Watchdog event: Throttle command timeout after 100ms");
          break;
        case dbw_mkz_msgs::WatchdogCounter::THROTTLE_REPORT:
          ROS_WARN("Watchdog event: Throttle report timeout after 100ms");
          break;
        case dbw_mkz_msgs::WatchdogCounter::STEERING_COUNTER:
          ROS_WARN("Watchdog event: Steering command counter failed to increment");
          break;
        case dbw_mkz_msgs::WatchdogCounter::STEERING_DISABLED:
          ROS_WARN("Watchdog event: Steering transition to disabled while in gear or moving");
          break;
        case dbw_mkz_msgs::WatchdogCounter::STEERING_COMMAND:
          ROS_WARN("Watchdog event: Steering command timeout after 100ms");
          break;
        case dbw_mkz_msgs::WatchdogCounter::STEERING_REPORT:
          ROS_WARN("Watchdog event: Steering report timeout after 100ms");
          break;
      }
      fault_watchdog_warned_ = true;
  } else if (!fault) {
    fault_watchdog_warned_ = false;
  }
  fault_watchdog_using_brakes_ = braking;
  if (fault && !fault_watchdog_using_brakes_ && fault_watchdog_warned_) {
    ROS_WARN_THROTTLE(2.0, "Watchdog event: Press left OK button on the steering wheel or cycle power to clear event.");
  }
}

void DbwNode::faultWatchdog(bool fault, uint8_t src) {
  faultWatchdog(fault, src, fault_watchdog_using_brakes_); // No change to 'using brakes' status
}

void DbwNode::publishJointStates(const ros::Time &stamp, const dbw_mkz_msgs::WheelSpeedReport *wheels, const dbw_mkz_msgs::SteeringReport *steering)
{
  double dt = (stamp - joint_state_.header.stamp).toSec();
  if (wheels) {
    joint_state_.velocity[JOINT_FL] = wheels->front_left;
    joint_state_.velocity[JOINT_FR] = wheels->front_right;
    joint_state_.velocity[JOINT_RL] = wheels->rear_left;
    joint_state_.velocity[JOINT_RR] = wheels->rear_right;
  }
  if (steering) {
    const double L = acker_wheelbase_;
    const double W = acker_track_;
    const double r = L / tan(steering->steering_wheel_angle / steering_ratio_);
    joint_state_.position[JOINT_SL] = atan(L / (r - W/2));
    joint_state_.position[JOINT_SR] = atan(L / (r + W/2));
  }
  if (dt < 0.5) {
    for (unsigned int i = JOINT_FL; i <= JOINT_RR; i++) {
      joint_state_.position[i] = fmod(joint_state_.position[i] + dt * joint_state_.velocity[i], 2*M_PI);
    }
  }
  joint_state_.header.stamp = stamp;
  pub_joint_states_.publish(joint_state_);
}

} // namespace dbw_mkz_can
