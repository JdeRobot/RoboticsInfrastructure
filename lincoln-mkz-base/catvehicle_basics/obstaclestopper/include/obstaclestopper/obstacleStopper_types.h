//
// Academic License - for use in teaching, academic research, and meeting
// course requirements at degree granting institutions only.  Not for
// government, commercial, or other organizational use.
//
// File: obstacleStopper_types.h
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
#ifndef RTW_HEADER_obstacleStopper_types_h_
#define RTW_HEADER_obstacleStopper_types_h_
#include "rtwtypes.h"
#ifndef DEFINED_TYPEDEF_FOR_SL_Bus_obstacleStopper_geometry_msgs_Vector3_
#define DEFINED_TYPEDEF_FOR_SL_Bus_obstacleStopper_geometry_msgs_Vector3_

// MsgType=geometry_msgs/Vector3
typedef struct {
  real_T X;
  real_T Y;
  real_T Z;
} SL_Bus_obstacleStopper_geometry_msgs_Vector3;

#endif

#ifndef DEFINED_TYPEDEF_FOR_SL_Bus_obstacleStopper_geometry_msgs_Twist_
#define DEFINED_TYPEDEF_FOR_SL_Bus_obstacleStopper_geometry_msgs_Twist_

// MsgType=geometry_msgs/Twist
typedef struct {
  // MsgType=geometry_msgs/Vector3
  SL_Bus_obstacleStopper_geometry_msgs_Vector3 Linear;

  // MsgType=geometry_msgs/Vector3
  SL_Bus_obstacleStopper_geometry_msgs_Vector3 Angular;
} SL_Bus_obstacleStopper_geometry_msgs_Twist;

#endif

#ifndef DEFINED_TYPEDEF_FOR_SL_Bus_obstacleStopper_std_msgs_Float32_
#define DEFINED_TYPEDEF_FOR_SL_Bus_obstacleStopper_std_msgs_Float32_

// MsgType=std_msgs/Float32
typedef struct {
  real32_T Data;
} SL_Bus_obstacleStopper_std_msgs_Float32;

#endif

#ifndef struct_tag_saG5948SFTrUFnIbVUb0TZH
#define struct_tag_saG5948SFTrUFnIbVUb0TZH

struct tag_saG5948SFTrUFnIbVUb0TZH
{
  int32_T isInitialized;
};

#endif                                 //struct_tag_saG5948SFTrUFnIbVUb0TZH

#ifndef typedef_robotics_slros_internal_block_T
#define typedef_robotics_slros_internal_block_T

typedef struct tag_saG5948SFTrUFnIbVUb0TZH robotics_slros_internal_block_T;

#endif                                 //typedef_robotics_slros_internal_block_T

#ifndef struct_tag_saG5948SFTrUFnIbVUb0TZH
#define struct_tag_saG5948SFTrUFnIbVUb0TZH

struct tag_saG5948SFTrUFnIbVUb0TZH
{
  int32_T isInitialized;
};

#endif                                 //struct_tag_saG5948SFTrUFnIbVUb0TZH

#ifndef typedef_robotics_slros_internal_blo_f_T
#define typedef_robotics_slros_internal_blo_f_T

typedef struct tag_saG5948SFTrUFnIbVUb0TZH robotics_slros_internal_blo_f_T;

#endif                                 //typedef_robotics_slros_internal_blo_f_T

#ifndef typedef_struct_T_obstacleStopper_T
#define typedef_struct_T_obstacleStopper_T

typedef struct {
  char_T f0[4];
} struct_T_obstacleStopper_T;

#endif                                 //typedef_struct_T_obstacleStopper_T

#ifndef typedef_struct_T_obstacleStopper_f_T
#define typedef_struct_T_obstacleStopper_f_T

typedef struct {
  char_T f0[8];
} struct_T_obstacleStopper_f_T;

#endif                                 //typedef_struct_T_obstacleStopper_f_T

#ifndef typedef_struct_T_obstacleStopper_ft_T
#define typedef_struct_T_obstacleStopper_ft_T

typedef struct {
  char_T f0[7];
} struct_T_obstacleStopper_ft_T;

#endif                                 //typedef_struct_T_obstacleStopper_ft_T

#ifndef typedef_struct_T_obstacleStopper_fto_T
#define typedef_struct_T_obstacleStopper_fto_T

typedef struct {
  char_T f0[8];
  char_T f1[7];
  char_T f2[6];
} struct_T_obstacleStopper_fto_T;

#endif                                 //typedef_struct_T_obstacleStopper_fto_T

// Parameters (auto storage)
typedef struct P_obstacleStopper_T_ P_obstacleStopper_T;

// Forward declaration for rtModel
typedef struct tag_RTM_obstacleStopper_T RT_MODEL_obstacleStopper_T;

#endif                                 // RTW_HEADER_obstacleStopper_types_h_

//
// File trailer for generated code.
//
// [EOF]
//
