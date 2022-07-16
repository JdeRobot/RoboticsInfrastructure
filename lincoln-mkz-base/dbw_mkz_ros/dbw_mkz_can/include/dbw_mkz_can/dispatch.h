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

#ifndef _DISPATCH_H
#define _DISPATCH_H
#include <stdint.h>

typedef struct {
  uint16_t PCMD;
  uint8_t BCMD :1;
  uint8_t :7;
  uint8_t EN :1;
  uint8_t CLEAR :1;
  uint8_t IGNORE :1;
  uint8_t :5;
  uint8_t :8;
  uint8_t :8;
  uint8_t :8;
  uint8_t count;
} MsgBrakeCmd;

typedef struct {
  uint16_t PI;
  uint16_t PC;
  uint16_t PO;
  uint8_t BO :1;
  uint8_t BC :1;
  uint8_t BI :1;
  uint8_t WDCBRK :1;
  uint8_t WDCSRC :4;
  uint8_t ENABLED :1;
  uint8_t OVERRIDE :1;
  uint8_t DRIVER :1;
  uint8_t FLTWDC :1;
  uint8_t FLT1 :1;
  uint8_t FLT2 :1;
  uint8_t FLTB :1;
  uint8_t FLTCON :1;
} MsgBrakeReport;

typedef struct {
  uint16_t PCMD;
  uint8_t :8;
  uint8_t EN :1;
  uint8_t CLEAR :1;
  uint8_t IGNORE :1;
  uint8_t :5;
  uint8_t :8;
  uint8_t :8;
  uint8_t :8;
  uint8_t count;
} MsgThrottleCmd;

typedef struct {
  uint16_t PI;
  uint16_t PC;
  uint16_t PO;
  uint8_t :4;
  uint8_t WDCSRC :4;
  uint8_t ENABLED :1;
  uint8_t OVERRIDE :1;
  uint8_t DRIVER :1;
  uint8_t FLTWDC :1;
  uint8_t FLT1 :1;
  uint8_t FLT2 :1;
  uint8_t :1;
  uint8_t FLTCON :1;
} MsgThrottleReport;

typedef struct {
  int16_t SCMD;
  uint8_t EN :1;
  uint8_t CLEAR :1;
  uint8_t IGNORE :1;
  uint8_t :1;
  uint8_t QUIET :1;
  uint8_t :3;
  uint8_t SVEL;
  uint8_t :8;
  uint8_t :8;
  uint8_t :8;
  uint8_t count;
} MsgSteeringCmd;

typedef struct {
  int16_t ANGLE;
  int16_t CMD;
  uint16_t SPEED;
  int8_t TORQUE;
  uint8_t ENABLED :1;
  uint8_t OVERRIDE :1;
  uint8_t DRIVER :1;
  uint8_t FLTWDC :1;
  uint8_t FLTBUS1 :1;
  uint8_t FLTBUS2 :1;
  uint8_t FLTCAL :1;
  uint8_t FLTCON :1;
} MsgSteeringReport;

typedef struct {
  uint8_t GCMD :3;
  uint8_t :4;
  uint8_t CLEAR :1;
} MsgGearCmd;

typedef struct {
  uint8_t STATE :3;
  uint8_t OVERRIDE :1;
  uint8_t CMD :3;
  uint8_t FLTBUS :1;
} MsgGearReport;

typedef struct {
  uint8_t TRNCMD :2;
  uint8_t :6;
} MsgTurnSignalCmd;

typedef struct {
  uint8_t turn_signal :2;
  uint8_t head_light_hi :2;
  uint8_t wiper_front :4;
  uint8_t light_ambient :3;
  uint8_t btn_cc_on :1;
  uint8_t btn_cc_off :1;
  uint8_t btn_cc_res:1;
  uint8_t btn_cc_cncl:1;
  uint8_t :1;
  uint8_t btn_cc_on_off :1;
  uint8_t btn_cc_res_cncl:1;
  uint8_t btn_cc_set_inc :1;
  uint8_t btn_cc_set_dec :1;
  uint8_t btn_cc_gap_inc :1;
  uint8_t btn_cc_gap_dec :1;
  uint8_t btn_la_on_off :1;
  uint8_t FLTBUS :1;
  uint8_t door_driver :1;
  uint8_t door_passenger :1;
  uint8_t door_rear_left :1;
  uint8_t door_rear_right :1;
  uint8_t door_hood :1;
  uint8_t door_trunk :1;
  uint8_t pasngr_detect :1;
  uint8_t pasngr_airbag :1;
  uint8_t buckle_driver :1;
  uint8_t buckle_pasngr :1;
  uint8_t :6;
} MsgMiscReport;

typedef struct {
  int16_t front_left;
  int16_t front_right;
  int16_t rear_left;
  int16_t rear_right;
} MsgReportWheelSpeed;

typedef struct {
  int16_t accel_lat;
  int16_t accel_long;
  int16_t accel_vert;
} MsgReportAccel;

typedef struct {
  int16_t gyro_roll;
  int16_t gyro_yaw;
} MsgReportGyro;

typedef struct {
  int32_t latitude :31;
  int32_t lat_valid :1;
  int32_t longitude :31;
  int32_t long_valid :1;
} MsgReportGps1;

typedef struct {
  uint8_t utc_year :7;
  uint8_t :1;
  uint8_t utc_month :4;
  uint8_t :4;
  uint8_t utc_day :5;
  uint8_t :3;
  uint8_t utc_hours :5;
  uint8_t :3;
  uint8_t utc_minutes :6;
  uint8_t :2;
  uint8_t utc_seconds :6;
  uint8_t :2;
  uint8_t compass_dir :4;
  uint8_t :4;
  uint8_t pdop :5;
  uint8_t fault :1;
  uint8_t inferred :1;
  uint8_t :1;
} MsgReportGps2;

typedef struct {
  int16_t altitude;
  uint16_t heading;
  uint8_t speed;
  uint8_t hdop;
  uint8_t vdop;
  uint8_t quality :3;
  uint8_t num_sats :5;
} MsgReportGps3;

typedef struct {
  int16_t front_left;
  int16_t front_right;
  int16_t rear_left;
  int16_t rear_right;
} MsgReportSuspension;

typedef struct {
  uint16_t front_left;
  uint16_t front_right;
  uint16_t rear_left;
  uint16_t rear_right;
} MsgReportTirePressure;

typedef struct {
  int16_t fuel_level;
} MsgReportFuelLevel;

typedef struct {
  uint8_t l_cta_alert :1;
  uint8_t l_cta_enabled :1;
  uint8_t l_blis_alert :1;
  uint8_t l_blis_enabled :1;
  uint8_t r_cta_alert :1;
  uint8_t r_cta_enabled :1;
  uint8_t r_blis_alert :1;
  uint8_t r_blis_enabled :1;
  uint8_t sonar_00 :4;
  uint8_t sonar_01 :4;
  uint8_t sonar_02 :4;
  uint8_t sonar_03 :4;
  uint8_t sonar_04 :4;
  uint8_t sonar_05 :4;
  uint8_t sonar_06 :4;
  uint8_t sonar_07 :4;
  uint8_t sonar_08 :4;
  uint8_t sonar_09 :4;
  uint8_t sonar_10 :4;
  uint8_t sonar_11 :4;
  uint8_t :6;
  uint8_t sonar_enabled :1;
  uint8_t sonar_fault :1;
} MsgReportSurround;

typedef struct {
  uint16_t brake_torque_request :12;
  uint16_t hsa_stat :3;
  uint16_t stationary :1;
  uint16_t brake_torque_actual :12;
  uint16_t hsa_mode :2;
  uint16_t parking_brake :2;
  int16_t wheel_torque :14;
  uint16_t :2;
  int16_t accel_over_ground_est :10;
  uint16_t abs_active :1;
  uint16_t abs_enabled :1;
  uint16_t stab_active :1;
  uint16_t stab_enabled :1;
  uint16_t trac_active :1;
  uint16_t trac_enabled :1;
} MsgReportBrakeInfo;

typedef struct {
  uint16_t engine_rpm :16;
  uint16_t throttle_pc :10;
  uint16_t :6;
  int16_t throttle_rate :8;
  uint16_t :8;
  uint16_t :8;
  uint16_t :8;
} MsgReportThrottleInfo;

enum {
    VERSION_BPEC = 1,
    VERSION_TPEC = 2,
    VERSION_EPAS = 3,
};
typedef struct {
  uint8_t module;
  uint8_t :8;
  uint16_t major;
  uint16_t minor;
  uint16_t build;
} MsgVersion;

#define BUILD_ASSERT(cond) do { (void) sizeof(char [1 - 2*!(cond)]); } while(0)
static void dispatchAssertSizes() {
  BUILD_ASSERT(8 == sizeof(MsgBrakeCmd));
  BUILD_ASSERT(8 == sizeof(MsgBrakeReport));
  BUILD_ASSERT(8 == sizeof(MsgThrottleCmd));
  BUILD_ASSERT(8 == sizeof(MsgThrottleReport));
  BUILD_ASSERT(8 == sizeof(MsgSteeringCmd));
  BUILD_ASSERT(8 == sizeof(MsgSteeringReport));
  BUILD_ASSERT(1 == sizeof(MsgGearCmd));
  BUILD_ASSERT(1 == sizeof(MsgGearReport));
  BUILD_ASSERT(1 == sizeof(MsgTurnSignalCmd));
  BUILD_ASSERT(5 == sizeof(MsgMiscReport));
  BUILD_ASSERT(8 == sizeof(MsgReportWheelSpeed));
  BUILD_ASSERT(6 == sizeof(MsgReportAccel));
  BUILD_ASSERT(4 == sizeof(MsgReportGyro));
  BUILD_ASSERT(8 == sizeof(MsgReportGps1));
  BUILD_ASSERT(8 == sizeof(MsgReportGps2));
  BUILD_ASSERT(8 == sizeof(MsgReportGps3));
  BUILD_ASSERT(8 == sizeof(MsgReportSuspension));
  BUILD_ASSERT(8 == sizeof(MsgReportTirePressure));
  BUILD_ASSERT(2 == sizeof(MsgReportFuelLevel));
  BUILD_ASSERT(8 == sizeof(MsgReportSurround));
  BUILD_ASSERT(8 == sizeof(MsgReportBrakeInfo));
  BUILD_ASSERT(8 == sizeof(MsgReportThrottleInfo));
  BUILD_ASSERT(8 == sizeof(MsgVersion));
}
#undef BUILD_ASSERT

enum {
  ID_BRAKE_CMD            = 0x060,
  ID_BRAKE_REPORT         = 0x061,
  ID_THROTTLE_CMD         = 0x062,
  ID_THROTTLE_REPORT      = 0x063,
  ID_STEERING_CMD         = 0x064,
  ID_STEERING_REPORT      = 0x065,
  ID_GEAR_CMD             = 0x066,
  ID_GEAR_REPORT          = 0x067,
  ID_MISC_CMD             = 0x068,
  ID_MISC_REPORT          = 0x069,
  ID_REPORT_WHEEL_SPEED   = 0x06A,
  ID_REPORT_ACCEL         = 0x06B,
  ID_REPORT_GYRO          = 0x06C,
  ID_REPORT_GPS1          = 0x06D,
  ID_REPORT_GPS2          = 0x06E,
  ID_REPORT_GPS3          = 0x06F,
  ID_REPORT_SUSPENSION    = 0x070,
  ID_REPORT_TIRE_PRESSURE = 0x071,
  ID_REPORT_FUEL_LEVEL    = 0x072,
  ID_REPORT_SURROUND      = 0x073,
  ID_REPORT_BRAKE_INFO    = 0x074,
  ID_REPORT_THROTTLE_INFO = 0x075,
  ID_VERSION              = 0x07F,
};

#endif // _DISPATCH_H
