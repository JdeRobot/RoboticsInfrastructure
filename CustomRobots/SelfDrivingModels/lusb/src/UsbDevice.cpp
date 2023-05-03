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

#include "lusb/UsbDevice.h"
#include <libusb-1.0/libusb.h>

using namespace std;

namespace lusb
{

static inline UsbDevice::Location locationFromLibUsbDevice(libusb_device *dev) {
  return UsbDevice::Location(libusb_get_bus_number(dev),
                             libusb_get_port_number(dev),
                             libusb_get_device_address(dev));
}

bool UsbDevice::handleError(int err)
{
  bool success;
  switch ((libusb_error)err) {
    case LIBUSB_SUCCESS:
      success = true;
      break;
    case LIBUSB_ERROR_TIMEOUT:
      success = false;
      break;
    case LIBUSB_ERROR_BUSY:
    case LIBUSB_ERROR_OVERFLOW:
    case LIBUSB_ERROR_INVALID_PARAM:
    case LIBUSB_ERROR_INTERRUPTED:
    case LIBUSB_ERROR_NO_MEM:
    case LIBUSB_ERROR_PIPE:
      throwError(err);
      success = false;
      break;
    case LIBUSB_ERROR_IO:
    case LIBUSB_ERROR_ACCESS:
    case LIBUSB_ERROR_NO_DEVICE:
    case LIBUSB_ERROR_NOT_FOUND:
    case LIBUSB_ERROR_NOT_SUPPORTED:
    case LIBUSB_ERROR_OTHER:
    default:
      closeDevice();
      throwError(err);
      success = false;
      break;
  }
  return success;
}
void UsbDevice::throwError(int err)
{
  error_code_ = (libusb_error)err;
  error_str_ = libusb_error_name(err);
  if (throw_errors_) {
    throw lusb::UsbDeviceException((libusb_error)err, error_str_.c_str());
  }
}
int UsbDevice::getLastError(std::string &str) const
{
  str = error_str_;
  return error_code_;
}
void UsbDevice::setDebugLevel(uint8_t level)
{
  if (level > LIBUSB_LOG_LEVEL_DEBUG) {
    level = LIBUSB_LOG_LEVEL_DEBUG;
  }
  libusb_set_debug(ctx_, level);
}

void UsbDevice::init()
{
  open_ = false;
  location_ = Location();
  libusb_handle_ = NULL;
  throw_errors_ = false;
  memset(bulk_threads_enable_, 0x00, sizeof(bulk_threads_enable_));
  memset(interrupt_threads_enable_, 0x00, sizeof(interrupt_threads_enable_));
  ctx_ = NULL;
  libusb_init(&ctx_);
  libusb_set_debug(ctx_, LIBUSB_LOG_LEVEL_NONE);
}

UsbDevice::UsbDevice(uint16_t vid, uint16_t pid, uint8_t mi)
{
  init();
  setDevceIds(vid, pid, mi);
}
UsbDevice::UsbDevice(uint16_t vid, uint16_t pid)
{
  init();
  setDevceIds(vid, pid, 0x00);
}
UsbDevice::UsbDevice()
{
  init();
  setDevceIds(0x0000, 0x0000, 0x00);
}
UsbDevice::~UsbDevice()
{
  close();
  if (ctx_) {
    libusb_exit(ctx_);
    ctx_ = NULL;
  }
}

void UsbDevice::setDevceIds(uint16_t vid, uint16_t pid, uint8_t mi)
{
  pid_ = pid;
  vid_ = vid;
  mi_ = mi;
}

void UsbDevice::listDevices(uint16_t vid, uint16_t pid, std::vector<Location> &vec)
{
  vec.clear();

  libusb_context *ctx = NULL;
  libusb_init(&ctx);
  libusb_set_debug(ctx, LIBUSB_LOG_LEVEL_NONE);

  libusb_device **list;
  ssize_t cnt = libusb_get_device_list(ctx, &list);
  if (cnt > 0) {
    for (ssize_t i = 0; i < cnt; i++) {
      libusb_device *device = list[i];
      struct libusb_device_descriptor desc;
      if (libusb_get_device_descriptor(device, &desc) == LIBUSB_SUCCESS) {
        if ((!vid || vid == desc.idVendor) && (!pid || pid == desc.idProduct)) {
          vec.push_back(locationFromLibUsbDevice(device));
        }
      }
    }
  }
  libusb_free_device_list(list, 1);

  libusb_exit(ctx);
}

bool UsbDevice::open(const Location &location)
{
  closeDevice();

  libusb_device **list;
  ssize_t cnt = libusb_get_device_list(ctx_, &list);
  ssize_t i = 0;
  if (cnt > 0) {
    for (i = 0; i < cnt; i++) {
      libusb_device *device = list[i];
      struct libusb_device_descriptor desc;
      if (libusb_get_device_descriptor(device, &desc) == LIBUSB_SUCCESS) {
        if ((!vid_ || vid_ == desc.idVendor) && (!pid_ || pid_ == desc.idProduct)) {
          Location loc = locationFromLibUsbDevice(device);
          if (location.match(loc)) {
            libusb_device_handle *handle;
            if (libusb_open(device, &handle) == LIBUSB_SUCCESS) {
              if (libusb_kernel_driver_active(handle, mi_) == 1) {
                libusb_detach_kernel_driver(handle, mi_);
              }
              if (libusb_claim_interface(handle, mi_) == LIBUSB_SUCCESS) {
                location_ = loc;
                libusb_handle_ = handle;
                open_ = true;
                break;
              }
              libusb_close(handle);
            }
          }
        }
      }
    }
  }

  libusb_free_device_list(list, 1);
  return open_;
}

void UsbDevice::close()
{
  for (int i = 0; i < 128; i++) {
    bulk_threads_enable_[i] = false;
    interrupt_threads_enable_[i] = false;
  }
  closeDevice();
}

void UsbDevice::closeDevice()
{
  if (open_) {
    open_ = false;
    if (libusb_handle_) {
      libusb_release_interface(libusb_handle_, 0);
      libusb_close(libusb_handle_);
    }
  }
  libusb_handle_ = NULL;
}

bool UsbDevice::bulkWrite(const void * data, int size, unsigned char endpoint, int timeout)
{
  if ((libusb_handle_ == NULL) || !open_) {
    return false;
  }
  int actual = 0;
  int err = libusb_bulk_transfer(libusb_handle_, endpoint & ~LIBUSB_ENDPOINT_IN, (unsigned char *)data, size, &actual,
                                 timeout);
  bool success;
  success = handleError(err);
  success &= size == actual;
  return success;
}
int UsbDevice::bulkRead(void * data, int size, unsigned char endpoint, int timeout)
{
  if ((libusb_handle_ == NULL) || !open_) {
    return -1;
  }
  int actual = 0;
  int err = libusb_bulk_transfer(libusb_handle_, endpoint | LIBUSB_ENDPOINT_IN, (unsigned char *)data, size, &actual,
                                 timeout);
  return handleError(err) ? actual : -1;
}
bool UsbDevice::interruptWrite(const void * data, int size, unsigned char endpoint, int timeout)
{
  if ((libusb_handle_ == NULL) || !open_) {
    return false;
  }
  int actual = 0;
  int err = libusb_interrupt_transfer(libusb_handle_, endpoint & ~LIBUSB_ENDPOINT_IN, (unsigned char *)data, size,
                                      &actual, timeout);
  bool success;
  success = handleError(err);
  success &= size == actual;
  return success;
}
int UsbDevice::interruptRead(void * data, int size, unsigned char endpoint, int timeout)
{
  if ((libusb_handle_ == NULL) || !open_) {
    return -1;
  }
  int actual = 0;
  int err = libusb_interrupt_transfer(libusb_handle_, endpoint | LIBUSB_ENDPOINT_IN, (unsigned char *)data, size,
                                      &actual, timeout);
  return handleError(err) ? actual : -1;
}

void UsbDevice::bulkReadThread(Callback callback, unsigned char endpoint)
{
  endpoint &= 0x7F;
  int size;
  char data[1024];
  while (bulk_threads_enable_[endpoint]) {
    if (open_) {
      size = bulkRead(data, sizeof(data), endpoint, 100);
      if (size > 0) {
        callback(data, size);
      }
    } else {
      bulk_threads_enable_[endpoint] = 0;
      return;
    }
  }
}
void UsbDevice::interruptReadThread(Callback callback, unsigned char endpoint)
{
  endpoint &= 0x7F;
  int size;
  char data[1024];
  while (interrupt_threads_enable_[endpoint]) {
    if (open_) {
      size = interruptRead(data, sizeof(data), endpoint, 100);
      if (size > 0) {
        callback(data, size);
      }
    } else {
      interrupt_threads_enable_[endpoint] = false;
      return;
    }
  }
}

void UsbDevice::stopBulkReadThread(unsigned char endpoint)
{
  endpoint &= 0x7F;
  bulk_threads_enable_[endpoint] = false;
  if (bulk_threads_[endpoint].joinable()) {
    bulk_threads_[endpoint].join();
  }
}
void UsbDevice::startBulkReadThread(Callback callback, unsigned char endpoint)
{
  endpoint &= 0x7F;
  stopBulkReadThread(endpoint);
  bulk_threads_enable_[endpoint] = true;
  bulk_threads_[endpoint] = boost::thread(&UsbDevice::bulkReadThread, this, callback, endpoint);
}
void UsbDevice::stopInterruptReadThread(unsigned char endpoint)
{

  endpoint &= 0x7F;
  interrupt_threads_enable_[endpoint] = false;
  if (interrupt_threads_[endpoint].joinable()) {
    interrupt_threads_[endpoint].join();
  }
}
void UsbDevice::startinterruptReadThread(Callback callback, unsigned char endpoint)
{
  endpoint &= 0x7F;
  stopBulkReadThread(endpoint);
  interrupt_threads_enable_[endpoint] = true;
  interrupt_threads_[endpoint] = boost::thread(&UsbDevice::interruptReadThread, this, callback, endpoint);
}

} //namespace lusb
