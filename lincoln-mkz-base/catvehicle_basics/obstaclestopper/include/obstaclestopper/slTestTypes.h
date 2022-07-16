/* Copyright 2013-2015 The MathWorks, Inc. */

#ifndef slTestTypesH
#define slTestTypesH

#ifdef SUPPORTS_PRAGMA_ONCE
#pragma once
#endif

#ifndef MATLAB_MEX_FILE
#ifndef BUILDING_STATEFLOW
#include "rt_mxclassid.h"
#endif
#endif

typedef struct slTestBlkInfo {
    char* blkPath;
    int blkId;
    void* targetSpecificInfo;
    char* mdlRefFullPath;
} slTestBlkInfo_t;

#endif
