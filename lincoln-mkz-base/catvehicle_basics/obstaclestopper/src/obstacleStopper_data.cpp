//
// Academic License - for use in teaching, academic research, and meeting
// course requirements at degree granting institutions only.  Not for
// government, commercial, or other organizational use.
//
// File: obstacleStopper_data.cpp
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
#include "obstacleStopper.h"
#include "obstacleStopper_private.h"

// Block parameters (auto storage)
P_obstacleStopper_T obstacleStopper_P = {
  0.02,                                // Mask Parameter: DeadMansSwitch_stepSize
                                       //  Referenced by: '<S2>/Simulate step size'

  0.2,                                 // Mask Parameter: DeadMansSwitch_timeout
                                       //  Referenced by: '<S2>/Timeout in seconds'


  {
    {
      0.0,                             // X
      0.0,                             // Y
      0.0                              // Z
    },                                 // Linear

    {
      0.0,                             // X
      0.0,                             // Y
      0.0                              // Z
    }                                  // Angular
  },                                   // Computed Parameter: Out1_Y0
                                       //  Referenced by: '<S9>/Out1'


  {
    {
      0.0,                             // X
      0.0,                             // Y
      0.0                              // Z
    },                                 // Linear

    {
      0.0,                             // X
      0.0,                             // Y
      0.0                              // Z
    }                                  // Angular
  },                                   // Computed Parameter: Constant_Value
                                       //  Referenced by: '<S6>/Constant'


  {
    {
      0.0,                             // X
      0.0,                             // Y
      0.0                              // Z
    },                                 // Linear

    {
      0.0,                             // X
      0.0,                             // Y
      0.0                              // Z
    }                                  // Angular
  },                                   // Computed Parameter: Constant_Value_h
                                       //  Referenced by: '<S1>/Constant'

  5.0,                                 // Expression: 5
                                       //  Referenced by: '<S3>/Constant'

  1.0,                                 // Expression: 1
                                       //  Referenced by: '<S3>/Saturation'

  0.0,                                 // Expression: 0
                                       //  Referenced by: '<S3>/Saturation'


  {
    0.0F                               // Data
  },                                   // Computed Parameter: Out1_Y0_h
                                       //  Referenced by: '<S8>/Out1'


  {
    0.0F                               // Data
  }                                    // Computed Parameter: Constant_Value_o
                                       //  Referenced by: '<S5>/Constant'

};

//
// File trailer for generated code.
//
// [EOF]
//
