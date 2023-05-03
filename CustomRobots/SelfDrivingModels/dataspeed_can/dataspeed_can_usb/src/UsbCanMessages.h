/*********************************************************************
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2015-2017, Dataspeed Inc.
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

#ifndef _USB_CAN_MESSAGES_H
#define _USB_CAN_MESSAGES_H
#include <stdint.h>

#if defined(__linux__) || defined(_WIN32)
    #define PACK_ATTRIB
    #pragma pack(push, 1)
#else
    #define PACK_ATTRIB	__attribute__ ((packed))
#endif

// Throw compiler errors on bad message sizes
#define BUILD_ASSERT(cond) do { (void) sizeof(char [1 - 2*!(cond)]); } while(0)

#define COMMS_VERSION 1

#define USB_VID  0x6923
#define USB_PID  0x0112
#define USB_MI   0

/*******************************************************************************
 * Common Structures and Unions
 ******************************************************************************/
typedef struct PACK_ATTRIB {
    uint16_t major;
    uint16_t minor;
    uint16_t build;
} Version; // 6 bytes
typedef union PACK_ATTRIB {
	struct PACK_ATTRIB {
        union PACK_ATTRIB {
            struct PACK_ATTRIB {
                uint32_t id :29;
                uint32_t extended :1;
                uint32_t channel :2;
                uint32_t stamp :28;
                uint32_t dlc :4;
            };
            uint32_t headerWord[2];
        };
        union PACK_ATTRIB {
            uint8_t data[8];
            uint32_t dataWord[2];
        };
	};
	uint32_t messageWord[4];
} MessageBuffer; // 16 bytes
static inline void testCommonSizes() {
    BUILD_ASSERT(sizeof(Version) == 6);
    BUILD_ASSERT(sizeof(MessageBuffer) == 16);
}
/******************************************************************************/


/*******************************************************************************
 * Configuration Interface
 ******************************************************************************/
#define CONFIGURATION_ENDPOINT 1
enum {
    USB_ID_VERSION       = 0x00,
    USB_ID_REBOOT        = 0x01,
    USB_ID_RESET         = 0x08,
    USB_ID_SET_BUS_CFG   = 0x10,
    USB_ID_GET_BUS_CFG   = 0x11,
    USB_ID_SET_FILTER    = 0x12,
    USB_ID_GET_FILTER    = 0x13,
    USB_ID_NUM_CHANNELS  = 0x40,
    USB_ID_GET_TIME      = 0x41,
    USB_ID_GET_STATS     = 0x42,
};
typedef union PACK_ATTRIB {
    uint8_t msg_id;
    struct PACK_ATTRIB {
        uint8_t msg_id;
        uint8_t hw_rev;
        uint16_t comms;
        Version firmware;
        Version bootloader;
        uint32_t serial_number;
    } version;
    struct PACK_ATTRIB {
        uint8_t msg_id;
        uint8_t channel;
        uint16_t dummy;
        uint32_t bitrate;
    } bus_cfg;
    struct PACK_ATTRIB {
        uint8_t msg_id;
        uint8_t channel;
        uint8_t success;
        uint8_t :8;
        uint32_t mask;
        uint32_t match;
    } filter;
    struct PACK_ATTRIB {
        uint8_t msg_id;
        uint8_t num_channels;
    } num_channels;
    struct PACK_ATTRIB {
        uint8_t msg_id;
        uint8_t dummy8;
        uint16_t dummy16;
        uint32_t stamp;
    } time;
    struct PACK_ATTRIB {
        uint8_t msg_id;
        uint8_t clear;
        uint16_t dummy16;
        uint32_t rx_drops[4];
        uint32_t tx_drops[4];
    } stats;
} ConfigPacket;
static inline void testConfigurationInterfaceSizes() {
    BUILD_ASSERT(sizeof(ConfigPacket) <= 64);
}
/******************************************************************************/


/*******************************************************************************
 * Data Stream
 ******************************************************************************/
#define STREAM_ENDPOINT 2
typedef struct PACK_ATTRIB {
    MessageBuffer msg[4];
} StreamPacket;
static inline void testDataStreamSizes() {
    BUILD_ASSERT(sizeof(StreamPacket) <= 64);
}
/******************************************************************************/

#undef BUILD_ASSERT
#undef PACK_ATTRIB
#if defined(__linux__) || defined (_WIN32)
    #pragma pack(pop)	// Undo packing
#endif

#endif // _USB_CAN_MESSAGES_H
