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

#include <dataspeed_can_usb/CanUsb.h>
#include <lusb/UsbDevice.h>
#include <string.h>	// memcpy() and memset()
#include <sstream>

// Protocol definition
#include "UsbCanMessages.h"

#include <queue>
class TxQueue
{
public:
  TxQueue(size_t max_size) : max_size_(max_size) {}
  ~TxQueue() {}
  inline bool empty() const { return queue_.empty(); }
  inline size_t size() const { return queue_.size(); }
  inline MessageBuffer& front() { return queue_.front(); }
  inline const MessageBuffer& front() const { return queue_.front(); }
  inline MessageBuffer& back() { return queue_.back(); }
  inline const MessageBuffer& back() const { return queue_.back(); }
  inline bool push(const MessageBuffer& __x) {
    if (queue_.size() < max_size_) {
      queue_.push(__x);
      return true;
    }
    return false;
  }
  inline void pop() { queue_.pop(); }
  inline size_t maxSize() const { return max_size_; }
private:
  size_t max_size_;
  std::queue<MessageBuffer> queue_;
};

namespace dataspeed_can_usb
{

CanUsb::CanUsb(lusb::UsbDevice *dev) : ready_(false), heap_dev_(false), dev_(dev), recv_callback_(NULL), version_major_(0), version_minor_(0), version_build_(0), version_comms_(0), serial_number_(0), num_channels_(0)
{
  if (!dev_) {
    dev_ = new lusb::UsbDevice(USB_VID, USB_PID, USB_MI);
    heap_dev_ = true;
  }
  queue_ = new TxQueue(100);
}
CanUsb::~CanUsb()
{
  if (dev_) {
    if (dev_->isOpen()) {
      dev_->stopBulkReadThread(STREAM_ENDPOINT);
      dev_->close();
    }
    if (heap_dev_) {
      delete dev_;
    }
    dev_ = NULL;
  }
  if (queue_) {
    delete queue_;
    queue_ = NULL;
  }
}

bool CanUsb::configure()
{
  if (readVersion()) {
    if (getNumChannels()) {
      dev_->startBulkReadThread(boost::bind(&CanUsb::recvStream, this, _1, _2), STREAM_ENDPOINT);
      ready_ = true;
      return true;
    }
  }
  return false;
}
bool CanUsb::open()
{
  if (!isOpen()) {
    if (!dev_->isOpen()) {
      if (dev_->open()) {
        if (configure()) {
          return true;
        }
      }
      dev_->close();
    } else {
      if (configure()) {
        return true;
      }
    }
  }
  return isOpen();
}
bool CanUsb::isOpen()
{
  if (ready_) {
    if (dev_->isOpen()) {
      return true;
    } else {
      ready_ = false;
    }
  }
  return false;
}
void CanUsb::closeDevice()
{
  dev_->stopBulkReadThread(STREAM_ENDPOINT);
  dev_->close();
  ready_ = false;
}

bool CanUsb::readVersion()
{
  ConfigPacket packet;
  packet.msg_id = USB_ID_VERSION;
  if (writeConfig(&packet, sizeof(packet.msg_id))) {
    int len = readConfig(&packet, sizeof(packet));
    if ((len >= (int)sizeof(packet.version)) && (packet.msg_id == USB_ID_VERSION)) {
      version_major_ = packet.version.firmware.major;
      version_minor_ = packet.version.firmware.minor;
      version_build_ = packet.version.firmware.build;
      version_comms_ = packet.version.comms;
      serial_number_ = packet.version.serial_number;
      return true;
    }
  }
  return false;
}

bool CanUsb::getNumChannels()
{
  ConfigPacket packet;
  packet.msg_id = USB_ID_NUM_CHANNELS;
  if (writeConfig(&packet, sizeof(packet.msg_id))) {
    int len = readConfig(&packet, sizeof(packet));
    if ((len >= (int)sizeof(packet.num_channels)) && (packet.msg_id == USB_ID_NUM_CHANNELS)) {
      num_channels_ = packet.num_channels.num_channels;
      return true;
    }
  }
  return false;
}

void CanUsb::recvStream(const void *data, int size)
{
  if (recv_callback_) {
    const MessageBuffer *ptr = ((StreamPacket*)data)->msg;
    while (size >= sizeof(*ptr)) {
        size -= sizeof(*ptr);
        recv_callback_(ptr->channel, ptr->id, ptr->extended, ptr->dlc, ptr->data);
        ptr++;
    }
  }
}

bool CanUsb::reboot()
{
  ConfigPacket packet;
  packet.msg_id = USB_ID_REBOOT;
  if (writeConfig(&packet, sizeof(packet.msg_id))) {
    closeDevice();
    return true;
  }
  return false;
}

bool CanUsb::reset()
{
  ConfigPacket packet;
  packet.msg_id = USB_ID_RESET;
  if (writeConfig(&packet, sizeof(packet.msg_id))) {
    int len = readConfig(&packet, sizeof(packet), USB_DEFAULT_TIMEOUT);
    if ((len >= (int)sizeof(packet.msg_id)) && (packet.msg_id == USB_ID_RESET)) {
      return true;
    }
  }
  return false;
}

bool CanUsb::setBitrate(unsigned int channel, uint32_t bitrate)
{
  ConfigPacket packet;
  packet.msg_id = USB_ID_SET_BUS_CFG;
  packet.bus_cfg.channel = channel;
  packet.bus_cfg.bitrate = bitrate;
  if (writeConfig(&packet, sizeof(packet.bus_cfg))) {
    int len = readConfig(&packet, sizeof(packet), USB_DEFAULT_TIMEOUT);
    if ((len >= (int)sizeof(packet.bus_cfg)) && (packet.msg_id == USB_ID_GET_BUS_CFG)) {
      return true;
    }
  }
  return false;
}

bool CanUsb::addFilter(unsigned int channel, uint32_t mask, uint32_t match)
{
  ConfigPacket packet;
  packet.msg_id = USB_ID_SET_FILTER;
  packet.filter.channel = channel;
  packet.filter.mask = mask;
  packet.filter.match = match;
  if (writeConfig(&packet, sizeof(packet.filter))) {
    int len = readConfig(&packet, sizeof(packet), USB_DEFAULT_TIMEOUT);
    if ((len >= (int)sizeof(packet.filter)) && (packet.msg_id == USB_ID_SET_FILTER)) {
      if (packet.filter.success) {
        return true;
      }
    }
  }
  return false;
}

bool CanUsb::getStats(std::vector<unsigned int> &rx_drops, std::vector<unsigned int> &tx_drops, bool clear)
{
  ConfigPacket packet;
  packet.msg_id = USB_ID_GET_STATS;
  if (writeConfig(&packet, sizeof(packet.bus_cfg))) {
    int len = readConfig(&packet, sizeof(packet), USB_DEFAULT_TIMEOUT);
    if ((len >= (int)sizeof(packet.stats)) && (packet.msg_id == USB_ID_GET_STATS)) {
      unsigned int size = std::min(num_channels_, (unsigned int)MAX_CHANNELS);
      rx_drops.resize(size);
      tx_drops.resize(size);
      for (unsigned int i = 0; i < size; i++) {
        rx_drops[i] = packet.stats.rx_drops[i];
        tx_drops[i] = packet.stats.tx_drops[i];
      }
      return true;
    }
  }
  return false;
}

bool CanUsb::getTimeStamp(uint32_t &timestamp)
{
  ConfigPacket packet;
  packet.msg_id = USB_ID_GET_TIME;
  if (writeConfig(&packet, sizeof(packet.msg_id))) {
    int len = readConfig(&packet, sizeof(packet));
    if ((len >= (int)sizeof(packet.time)) && (packet.msg_id == USB_ID_GET_TIME)) {
      timestamp = packet.time.stamp;
      return true;
    }
  }
  return false;
}

void CanUsb::sendMessage(unsigned int channel, uint32_t id, bool extended, uint8_t dlc, const uint8_t data[8], bool flush)
{
  MessageBuffer msg;
  msg.headerWord[0] = 0;
  msg.headerWord[1] = 0;
  msg.id = id;
  msg.extended = extended ? 1 : 0;
  msg.channel = channel;
  msg.dlc = dlc;
  memcpy(msg.data, data, 8);
  queue_->push(msg);
  if (flush || (queue_->size() >= sizeof(StreamPacket) / sizeof(MessageBuffer))) {
    flushMessages();
  }
}
void CanUsb::flushMessages()
{
  if (!queue_->empty()) {
    unsigned int num = std::min(queue_->size(), sizeof(StreamPacket) / sizeof(MessageBuffer));
    if (writeStream(&queue_->front(), num * sizeof(MessageBuffer))) {
      while (num--) {
        queue_->pop();
      }
    }
  }
}

bool CanUsb::writeConfig(const void * data, int size)
{
  return writeConfig(data, size, USB_DEFAULT_TIMEOUT);
}
int CanUsb::readConfig(void * data, int size)
{
  return readConfig(data, size, USB_DEFAULT_TIMEOUT);
}
bool CanUsb::writeConfig(const void * data, int size, int timeout)
{
  if (!dev_->bulkWrite(data, size, CONFIGURATION_ENDPOINT, timeout)) {
    return false;
  }
  return true;
}
int CanUsb::readConfig(void * data, int size, int timeout)
{
  int len = dev_->bulkRead(data, size, CONFIGURATION_ENDPOINT, timeout);
  if (len < 0) {
    return -1;
  }
  return len;
}

bool CanUsb::writeStream(const void * data, int size)
{
  if (!dev_->bulkWrite(data, size, STREAM_ENDPOINT, USB_DEFAULT_TIMEOUT)) {
    return false;
  }
  return true;
}
int CanUsb::readStream(void * data, int size)
{
  int len = dev_->bulkRead(data, size, STREAM_ENDPOINT, USB_DEFAULT_TIMEOUT);
  if (len < 0) {
    return -1;
  }
  return len;
}

std::string CanUsb::version() const
{
  std::stringstream s;
  s << version_major_ << "." << version_minor_ << "." << version_build_ << "-" << version_comms_;
  return s.str();
}

} // namespace dataspeed_can_usb
