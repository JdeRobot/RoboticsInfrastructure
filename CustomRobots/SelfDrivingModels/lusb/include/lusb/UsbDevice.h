/*********************************************************************
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2014-2017, Dataspeed Inc.
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

#ifndef USB_DEVICE_H_
#define USB_DEVICE_H_

#include <stdexcept>
#include <string>
#include <boost/function.hpp>
#include <boost/thread.hpp>

struct libusb_device_handle;
struct libusb_context;

namespace lusb
{

struct UsbDeviceException : public std::runtime_error
{
  int error_code_;
  UsbDeviceException(int code, const char* msg) :
      std::runtime_error(msg), error_code_(code)
  {
  }
};

class UsbDevice
{
public:
  UsbDevice(uint16_t vid, uint16_t pid, uint8_t mi);
  UsbDevice(uint16_t vid, uint16_t pid);
  UsbDevice();
  ~UsbDevice();

  class Location {
  public:
    Location() : loc(0) {}
    Location(uint8_t _bus, uint8_t _port = 0, uint8_t _addr = 0) : loc(0) {
      bus = _bus;
      addr = _addr;
      port = _port;
    }
    static bool match(const Location& a, const Location& b) {
      // Equal to each other or zero
      return !((a.bus  && b.bus  && (a.bus  != b.bus )) ||
               (a.addr && b.addr && (a.addr != b.addr)) ||
               (a.port && b.port && (a.port != b.port)));
    }
    bool match(const Location& other) const {
      return match(*this, other);
    }
    bool operator==(const Location& other) const {
      return loc == other.loc;
    }
    bool operator!=(const Location& other) const {
      return loc != other.loc;
    }
    bool operator<(const Location& other) const {
      return loc < other.loc;
    }
    bool operator>(const Location& other) const {
      return loc > other.loc;
    }
    bool operator<=(const Location& other) const {
      return loc <= other.loc;
    }
    bool operator>=(const Location& other) const {
      return loc >= other.loc;
    }
    union { // Zero for don't care
      uint32_t loc;
      struct {
        uint8_t bus;  // Bus number
        uint8_t addr; // Address, unique for each bus, new on reconnect
        uint8_t port; // Port on parent hub, not unique for each bus
        uint8_t :8;
      };
    };
  };
  static void listDevices(uint16_t vid, uint16_t pid, std::vector<Location> &list);

  void setDevceIds(uint16_t vid, uint16_t pid, uint8_t mi);
  bool open(const Location &location = Location());
  void close();

  bool isOpen() const { return open_; }
  Location getLocation() const { return location_; }

  bool bulkWrite(const void * data, int size, unsigned char endpoint, int timeout);
  int bulkRead(void * data, int size, unsigned char endpoint, int timeout);
  bool interruptWrite(const void * data, int size, unsigned char endpoint, int timeout);
  int interruptRead(void * data, int size, unsigned char endpoint, int timeout);

  typedef boost::function<void(const void *data, int size)> Callback;
  void startBulkReadThread(Callback callback, unsigned char endpoint);
  void stopBulkReadThread(unsigned char endpoint);
  void startinterruptReadThread(Callback callback, unsigned char endpoint);
  void stopInterruptReadThread(unsigned char endpoint);

  bool throw_errors_;
  int getLastError(std::string &str) const;
  void setDebugLevel(uint8_t level);

private:
  bool handleError(int err);
  void throwError(int err);
  void init();
  void closeDevice();

  void bulkReadThread(Callback callback, unsigned char endpoint);
  void interruptReadThread(Callback callback, unsigned char endpoint);

  int error_code_;
  std::string error_str_;

  uint16_t vid_;
  uint16_t pid_;
  uint8_t mi_;
  bool open_;
  Location location_;
  libusb_device_handle *libusb_handle_;
  libusb_context *ctx_;
  boost::thread bulk_threads_[128];
  bool bulk_threads_enable_[128];
  boost::thread interrupt_threads_[128];
  bool interrupt_threads_enable_[128];

};
} //namespace lusb

#endif /* USB_DEVICE_H_ */
