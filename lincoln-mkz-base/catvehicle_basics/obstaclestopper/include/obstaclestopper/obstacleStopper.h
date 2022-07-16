//
// Academic License - for use in teaching, academic research, and meeting
// course requirements at degree granting institutions only.  Not for
// government, commercial, or other organizational use.
//
// File: obstacleStopper.h
//
// Code generated for Simulink model 'obstacleStopper'.
//
// Model version                  : 1.8
// Simulink Coder version         : 8.10 (R2016a) 10-Feb-2016
// C/C++ source code generated on : Fri Jan 27 11:14:49 2017
//
// Target selection: ert.tlc
// Embedded hardware selection: Generic->Unspecified (assume 32-bit Generic)
// Code generation objectives: Unspecified
// Validation result: Not run
//
#ifndef RTW_HEADER_obstacleStopper_h_
#define RTW_HEADER_obstacleStopper_h_
#include <stddef.h>
#include <string.h>
#ifndef obstacleStopper_COMMON_INCLUDES_
# define obstacleStopper_COMMON_INCLUDES_
#include "rtwtypes.h"
#include "slros_initialize.h"
#endif                                 // obstacleStopper_COMMON_INCLUDES_

#include "obstacleStopper_types.h"

// Macros for accessing real-time model data structure
#ifndef rtmGetErrorStatus
# define rtmGetErrorStatus(rtm)        ((rtm)->errorStatus)
#endif

#ifndef rtmSetErrorStatus
# define rtmSetErrorStatus(rtm, val)   ((rtm)->errorStatus = (val))
#endif

// Block signals (auto storage)
typedef struct {
  SL_Bus_obstacleStopper_geometry_msgs_Twist In1;// '<S9>/In1'
  SL_Bus_obstacleStopper_geometry_msgs_Twist BusAssignment;// '<Root>/Bus Assignment' 
  char_T cv0[35];
  SL_Bus_obstacleStopper_std_msgs_Float32 In1_d;// '<S8>/In1'
} B_obstacleStopper_T;

// Block states (auto storage) for system '<Root>'
typedef struct {
  real_T sinceLastMsg;                 // '<S2>/timeout set to 0 output'
  void *SourceBlock_PWORK;             // '<S6>/SourceBlock'
  void *SourceBlock_PWORK_b;           // '<S5>/SourceBlock'
  void *SinkBlock_PWORK;               // '<S4>/SinkBlock'
  robotics_slros_internal_block_T obj; // '<S4>/SinkBlock'
  robotics_slros_internal_blo_f_T obj_l;// '<S6>/SourceBlock'
  robotics_slros_internal_blo_f_T obj_e;// '<S5>/SourceBlock'
  boolean_T sinceLastMsg_not_empty;    // '<S2>/timeout set to 0 output'
} DW_obstacleStopper_T;

// Parameters (auto storage)
struct P_obstacleStopper_T_ {
  real_T DeadMansSwitch_stepSize;      // Mask Parameter: DeadMansSwitch_stepSize
                                       //  Referenced by: '<S2>/Simulate step size'

  real_T DeadMansSwitch_timeout;       // Mask Parameter: DeadMansSwitch_timeout
                                       //  Referenced by: '<S2>/Timeout in seconds'

  SL_Bus_obstacleStopper_geometry_msgs_Twist Out1_Y0;// Computed Parameter: Out1_Y0
                                                     //  Referenced by: '<S9>/Out1'

  SL_Bus_obstacleStopper_geometry_msgs_Twist Constant_Value;// Computed Parameter: Constant_Value
                                                            //  Referenced by: '<S6>/Constant'

  SL_Bus_obstacleStopper_geometry_msgs_Twist Constant_Value_h;// Computed Parameter: Constant_Value_h
                                                              //  Referenced by: '<S1>/Constant'

  real_T Constant_Value_e;             // Expression: 5
                                       //  Referenced by: '<S3>/Constant'

  real_T Saturation_UpperSat;          // Expression: 1
                                       //  Referenced by: '<S3>/Saturation'

  real_T Saturation_LowerSat;          // Expression: 0
                                       //  Referenced by: '<S3>/Saturation'

  SL_Bus_obstacleStopper_std_msgs_Float32 Out1_Y0_h;// Computed Parameter: Out1_Y0_h
                                                    //  Referenced by: '<S8>/Out1'

  SL_Bus_obstacleStopper_std_msgs_Float32 Constant_Value_o;// Computed Parameter: Constant_Value_o
                                                           //  Referenced by: '<S5>/Constant'

};

// Real-time Model Data Structure
struct tag_RTM_obstacleStopper_T {
  const char_T *errorStatus;
};

// Block parameters (auto storage)
#ifdef __cplusplus

extern "C" {

#endif

  extern P_obstacleStopper_T obstacleStopper_P;

#ifdef __cplusplus

}
#endif

// Block signals (auto storage)
extern B_obstacleStopper_T obstacleStopper_B;

// Block states (auto storage)
extern DW_obstacleStopper_T obstacleStopper_DW;

#ifdef __cplusplus

extern "C" {

#endif

#ifdef __cplusplus

}
#endif

#ifdef __cplusplus

extern "C" {

#endif

  // Model entry point functions
  extern void obstacleStopper_initialize(void);
  extern void obstacleStopper_step(void);
  extern void obstacleStopper_terminate(void);

#ifdef __cplusplus

}
#endif

// Real-time Model object
#ifdef __cplusplus

extern "C" {

#endif

  extern RT_MODEL_obstacleStopper_T *const obstacleStopper_M;

#ifdef __cplusplus

}
#endif

//-
//  The generated code includes comments that allow you to trace directly
//  back to the appropriate location in the model.  The basic format
//  is <system>/block_name, where system is the system number (uniquely
//  assigned by Simulink) and block_name is the name of the block.
//
//  Use the MATLAB hilite_system command to trace the generated code back
//  to the model.  For example,
//
//  hilite_system('<S3>')    - opens system 3
//  hilite_system('<S3>/Kp') - opens and selects block Kp which resides in S3
//
//  Here is the system hierarchy for this model
//
//  '<Root>' : 'obstacleStopper'
//  '<S1>'   : 'obstacleStopper/Blank Message'
//  '<S2>'   : 'obstacleStopper/Dead Man's Switch'
//  '<S3>'   : 'obstacleStopper/Obstacle Stopper'
//  '<S4>'   : 'obstacleStopper/Publish'
//  '<S5>'   : 'obstacleStopper/Subscribe'
//  '<S6>'   : 'obstacleStopper/Subscribe1'
//  '<S7>'   : 'obstacleStopper/Dead Man's Switch/timeout set to 0 output'
//  '<S8>'   : 'obstacleStopper/Subscribe/Enabled Subsystem'
//  '<S9>'   : 'obstacleStopper/Subscribe1/Enabled Subsystem'

#endif                                 // RTW_HEADER_obstacleStopper_h_

//
// File trailer for generated code.
//
// [EOF]
//
