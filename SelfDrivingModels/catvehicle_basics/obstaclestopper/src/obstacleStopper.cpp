//
// Academic License - for use in teaching, academic research, and meeting
// course requirements at degree granting institutions only.  Not for
// government, commercial, or other organizational use.
//
// File: obstacleStopper.cpp
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
#define obstacleStopper_MessageQueueLen (1)

// Block signals (auto storage)
B_obstacleStopper_T obstacleStopper_B;

// Block states (auto storage)
DW_obstacleStopper_T obstacleStopper_DW;

// Real-time model
RT_MODEL_obstacleStopper_T obstacleStopper_M_;
RT_MODEL_obstacleStopper_T *const obstacleStopper_M = &obstacleStopper_M_;

// Model step function
void obstacleStopper_step(void)
{
  boolean_T timedOut;
  SL_Bus_obstacleStopper_std_msgs_Float32 varargout_2;
  boolean_T varargout_1;
  real_T rtb_safeValue;
  real_T u0;

  // Outputs for Atomic SubSystem: '<Root>/Subscribe'
  // Start for MATLABSystem: '<S5>/SourceBlock' incorporates:
  //   Inport: '<S8>/In1'
  //   MATLABSystem: '<S5>/SourceBlock'

  varargout_1 = Sub_obstacleStopper_12.getLatestMessage(&varargout_2);

  // Outputs for Enabled SubSystem: '<S5>/Enabled Subsystem' incorporates:
  //   EnablePort: '<S8>/Enable'

  if (varargout_1) {
    obstacleStopper_B.In1_d = varargout_2;
  }

  // End of Start for MATLABSystem: '<S5>/SourceBlock'
  // End of Outputs for SubSystem: '<S5>/Enabled Subsystem'
  // End of Outputs for SubSystem: '<Root>/Subscribe'

  // Outputs for Atomic SubSystem: '<Root>/Subscribe1'
  // Start for MATLABSystem: '<S6>/SourceBlock' incorporates:
  //   Inport: '<S9>/In1'
  //   MATLABSystem: '<S6>/SourceBlock'

  varargout_1 = Sub_obstacleStopper_13.getLatestMessage
    (&obstacleStopper_B.BusAssignment);

  // Outputs for Enabled SubSystem: '<S6>/Enabled Subsystem' incorporates:
  //   EnablePort: '<S9>/Enable'

  if (varargout_1) {
    obstacleStopper_B.In1 = obstacleStopper_B.BusAssignment;
  }

  // End of Outputs for SubSystem: '<S6>/Enabled Subsystem'
  // End of Outputs for SubSystem: '<Root>/Subscribe1'

  // Outputs for Atomic SubSystem: '<Root>/Dead Man's Switch'
  // MATLAB Function: '<S2>/timeout set to 0 output' incorporates:
  //   MATLABSystem: '<S6>/SourceBlock'
  //   Start for MATLABSystem: '<S6>/SourceBlock'

  // MATLAB Function 'Dead Man\'s Switch/timeout set to 0 output': '<S7>:1'
  // '<S7>:1:4' timedOut=true;
  timedOut = true;

  // '<S7>:1:5' if isempty(sinceLastMsg)
  if (!obstacleStopper_DW.sinceLastMsg_not_empty) {
    // '<S7>:1:6' sinceLastMsg=(timeout/stepSize)+1;
    obstacleStopper_DW.sinceLastMsg = obstacleStopper_P.DeadMansSwitch_timeout /
      obstacleStopper_P.DeadMansSwitch_stepSize + 1.0;
    obstacleStopper_DW.sinceLastMsg_not_empty = true;
  }

  // '<S7>:1:9' safeValue=0;
  rtb_safeValue = 0.0;

  // Outputs for Atomic SubSystem: '<Root>/Subscribe1'
  //  if no new message
  //  after timeout, we output 0
  // '<S7>:1:12' if( isNew == true )
  if (varargout_1) {
    // '<S7>:1:13' sinceLastMsg = 0;
    obstacleStopper_DW.sinceLastMsg = 0.0;
  } else {
    // '<S7>:1:14' else
    // '<S7>:1:15' sinceLastMsg = sinceLastMsg+1;
    obstacleStopper_DW.sinceLastMsg++;
  }

  // End of Outputs for SubSystem: '<Root>/Subscribe1'
  //  Note: we require step size as an input here, and depend on our
  //  system being executed at a regular rate, or bad things will happen
  // '<S7>:1:20' if( sinceLastMsg < timeout/stepSize )
  if (obstacleStopper_DW.sinceLastMsg < obstacleStopper_P.DeadMansSwitch_timeout
      / obstacleStopper_P.DeadMansSwitch_stepSize) {
    // '<S7>:1:21' timedOut = false;
    timedOut = false;
  }

  // '<S7>:1:24' if( timedOut == false )
  if (!timedOut) {
    // '<S7>:1:25' safeValue = value;
    rtb_safeValue = obstacleStopper_B.In1.Linear.X;
  }

  // End of MATLAB Function: '<S2>/timeout set to 0 output'
  // End of Outputs for SubSystem: '<Root>/Dead Man's Switch'

  // BusAssignment: '<Root>/Bus Assignment' incorporates:
  //   Constant: '<S1>/Constant'

  obstacleStopper_B.BusAssignment = obstacleStopper_P.Constant_Value_h;

  // Sum: '<S3>/Subtract' incorporates:
  //   Constant: '<S3>/Constant'

  u0 = obstacleStopper_B.In1_d.Data - obstacleStopper_P.Constant_Value_e;

  // Saturate: '<S3>/Saturation'
  if (u0 > obstacleStopper_P.Saturation_UpperSat) {
    u0 = obstacleStopper_P.Saturation_UpperSat;
  } else {
    if (u0 < obstacleStopper_P.Saturation_LowerSat) {
      u0 = obstacleStopper_P.Saturation_LowerSat;
    }
  }

  // End of Saturate: '<S3>/Saturation'

  // Signum: '<S3>/Sign'
  if (u0 < 0.0) {
    u0 = -1.0;
  } else if (u0 > 0.0) {
    u0 = 1.0;
  } else {
    if (u0 == 0.0) {
      u0 = 0.0;
    }
  }

  // BusAssignment: '<Root>/Bus Assignment' incorporates:
  //   Product: '<S3>/Product'
  //   Signum: '<S3>/Sign'

  obstacleStopper_B.BusAssignment.Linear.X = u0 * rtb_safeValue;
  obstacleStopper_B.BusAssignment.Angular.Z = obstacleStopper_B.In1.Angular.Z;

  // Outputs for Atomic SubSystem: '<Root>/Publish'
  // Start for MATLABSystem: '<S4>/SinkBlock' incorporates:
  //   MATLABSystem: '<S4>/SinkBlock'

  Pub_obstacleStopper_17.publish(&obstacleStopper_B.BusAssignment);

  // End of Outputs for SubSystem: '<Root>/Publish'
}

// Model initialize function
void obstacleStopper_initialize(void)
{
  // Registration code

  // initialize error status
  rtmSetErrorStatus(obstacleStopper_M, (NULL));

  // block I/O
  (void) memset(((void *) &obstacleStopper_B), 0,
                sizeof(B_obstacleStopper_T));

  // states (dwork)
  (void) memset((void *)&obstacleStopper_DW, 0,
                sizeof(DW_obstacleStopper_T));

  {
    static const char_T tmp[24] = { '/', 'c', 'a', 't', 'v', 'e', 'h', 'i', 'c',
      'l', 'e', '/', 'c', 'm', 'd', '_', 'v', 'e', 'l', '_', 's', 'a', 'f', 'e'
    };

    static const char_T tmp_0[19] = { '/', 'c', 'a', 't', 'v', 'e', 'h', 'i',
      'c', 'l', 'e', '/', 'c', 'm', 'd', '_', 'v', 'e', 'l' };

    /*
    static const char_T tmp_1[34] = { '/', 'c', 'a', 't', 'v', 'e', 'h', 'i',
      'c', 'l', 'e', '/', 'd', 'i', 's', 't', 'a', 'n', 'c', 'e', 'E', 's', 't',
      'i', 'm', 'a', 't', 'o', 'r', '/', 'd', 'i', 's', 't' };
    */
    static const char_T tmp_1[34] = { '/', 'd', 'i', 's', 't', 'a', 'n', 'c', 'e', 'E', 's', 't',
      'i', 'm', 'a', 't', 'o', 'r', '/', 'd', 'i', 's', 't' };

    char_T tmp_2[25];
    char_T tmp_3[20];
    int32_T i;

    // Start for Atomic SubSystem: '<Root>/Subscribe'
    // Start for MATLABSystem: '<S5>/SourceBlock'
    obstacleStopper_DW.obj_e.isInitialized = 0;
    obstacleStopper_DW.obj_e.isInitialized = 1;
    for (i = 0; i < 34; i++) {
      obstacleStopper_B.cv0[i] = tmp_1[i];
    }

    obstacleStopper_B.cv0[34] = '\x00';
    Sub_obstacleStopper_12.createSubscriber(obstacleStopper_B.cv0,
      obstacleStopper_MessageQueueLen);

    // End of Start for MATLABSystem: '<S5>/SourceBlock'
    // End of Start for SubSystem: '<Root>/Subscribe'

    // Start for Atomic SubSystem: '<Root>/Subscribe1'
    // Start for MATLABSystem: '<S6>/SourceBlock'
    obstacleStopper_DW.obj_l.isInitialized = 0;
    obstacleStopper_DW.obj_l.isInitialized = 1;
    for (i = 0; i < 19; i++) {
      tmp_3[i] = tmp_0[i];
    }

    tmp_3[19] = '\x00';
    Sub_obstacleStopper_13.createSubscriber(tmp_3,
      obstacleStopper_MessageQueueLen);

    // End of Start for MATLABSystem: '<S6>/SourceBlock'
    // End of Start for SubSystem: '<Root>/Subscribe1'

    // Start for Atomic SubSystem: '<Root>/Publish'
    // Start for MATLABSystem: '<S4>/SinkBlock'
    obstacleStopper_DW.obj.isInitialized = 0;
    obstacleStopper_DW.obj.isInitialized = 1;
    for (i = 0; i < 24; i++) {
      tmp_2[i] = tmp[i];
    }

    tmp_2[24] = '\x00';
    Pub_obstacleStopper_17.createPublisher(tmp_2,
      obstacleStopper_MessageQueueLen);

    // End of Start for MATLABSystem: '<S4>/SinkBlock'
    // End of Start for SubSystem: '<Root>/Publish'

    // SystemInitialize for Atomic SubSystem: '<Root>/Subscribe'
    // SystemInitialize for Enabled SubSystem: '<S5>/Enabled Subsystem'
    // SystemInitialize for Outport: '<S8>/Out1'
    obstacleStopper_B.In1_d = obstacleStopper_P.Out1_Y0_h;

    // End of SystemInitialize for SubSystem: '<S5>/Enabled Subsystem'
    // End of SystemInitialize for SubSystem: '<Root>/Subscribe'

    // SystemInitialize for Atomic SubSystem: '<Root>/Subscribe1'
    // SystemInitialize for Enabled SubSystem: '<S6>/Enabled Subsystem'
    // SystemInitialize for Outport: '<S9>/Out1'
    obstacleStopper_B.In1 = obstacleStopper_P.Out1_Y0;

    // End of SystemInitialize for SubSystem: '<S6>/Enabled Subsystem'
    // End of SystemInitialize for SubSystem: '<Root>/Subscribe1'

    // SystemInitialize for Atomic SubSystem: '<Root>/Dead Man's Switch'
    // SystemInitialize for MATLAB Function: '<S2>/timeout set to 0 output'
    obstacleStopper_DW.sinceLastMsg_not_empty = false;

    // End of SystemInitialize for SubSystem: '<Root>/Dead Man's Switch'
  }
}

// Model terminate function
void obstacleStopper_terminate(void)
{
  // Terminate for Atomic SubSystem: '<Root>/Subscribe'
  // Start for MATLABSystem: '<S5>/SourceBlock' incorporates:
  //   Terminate for MATLABSystem: '<S5>/SourceBlock'

  if (obstacleStopper_DW.obj_e.isInitialized == 1) {
    obstacleStopper_DW.obj_e.isInitialized = 2;
  }

  // End of Start for MATLABSystem: '<S5>/SourceBlock'
  // End of Terminate for SubSystem: '<Root>/Subscribe'

  // Terminate for Atomic SubSystem: '<Root>/Subscribe1'
  // Start for MATLABSystem: '<S6>/SourceBlock' incorporates:
  //   Terminate for MATLABSystem: '<S6>/SourceBlock'

  if (obstacleStopper_DW.obj_l.isInitialized == 1) {
    obstacleStopper_DW.obj_l.isInitialized = 2;
  }

  // End of Start for MATLABSystem: '<S6>/SourceBlock'
  // End of Terminate for SubSystem: '<Root>/Subscribe1'

  // Terminate for Atomic SubSystem: '<Root>/Publish'
  // Start for MATLABSystem: '<S4>/SinkBlock' incorporates:
  //   Terminate for MATLABSystem: '<S4>/SinkBlock'

  if (obstacleStopper_DW.obj.isInitialized == 1) {
    obstacleStopper_DW.obj.isInitialized = 2;
  }

  // End of Start for MATLABSystem: '<S4>/SinkBlock'
  // End of Terminate for SubSystem: '<Root>/Publish'
}

//
// File trailer for generated code.
//
// [EOF]
//
