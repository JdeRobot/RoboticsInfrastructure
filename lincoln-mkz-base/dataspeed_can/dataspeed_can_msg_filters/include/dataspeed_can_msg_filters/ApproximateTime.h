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

#ifndef _CAN_APPROXIMATE_TIME_H_
#define _CAN_APPROXIMATE_TIME_H_

#include <deque>
#include <ros/ros.h>
#include <dataspeed_can_msgs/CanMessageStamped.h>

namespace dataspeed_can_msg_filters
{
class ApproximateTime
{
public:
  typedef dataspeed_can_msgs::CanMessageStamped::ConstPtr Type;
  typedef boost::function<void(const std::vector<Type> &vec)> Callback;

  ApproximateTime(uint32_t queue_size, Callback callback, uint32_t id1, uint32_t id2)
: queue_size_(queue_size)
, callback_(callback)
, num_non_empty_deques_(0)
, pivot_(NO_PIVOT)
, max_interval_duration_(ros::DURATION_MAX)
, age_penalty_(0.1)
  {
    ROS_ASSERT(queue_size_ > 0);  // The synchronizer will tend to drop many messages with a queue size of 1. At least 2 is recommended.

    std::vector<unsigned int> ids(2);
    ids[0] = id1;
    ids[1] = id2;

    vector_.resize(ids.size());
    for (unsigned int i = 0; i < ids.size(); i++) {
      vector_[i].id = ids[i];
      vector_[i].has_dropped_messages = false;
      vector_[i].inter_message_lower_bounds = ros::Duration(0);
      vector_[i].warned_about_incorrect_bound = false;
    }
  }
  ApproximateTime(uint32_t queue_size, Callback callback, uint32_t id1, uint32_t id2, uint32_t id3)
: queue_size_(queue_size)
, callback_(callback)
, num_non_empty_deques_(0)
, pivot_(NO_PIVOT)
, max_interval_duration_(ros::DURATION_MAX)
, age_penalty_(0.1)
  {
    ROS_ASSERT(queue_size_ > 0);  // The synchronizer will tend to drop many messages with a queue size of 1. At least 2 is recommended.

    std::vector<unsigned int> ids(3);
    ids[0] = id1;
    ids[1] = id2;
    ids[2] = id3;

    vector_.resize(ids.size());
    for (unsigned int i = 0; i < ids.size(); i++) {
      vector_[i].id = ids[i];
      vector_[i].has_dropped_messages = false;
      vector_[i].inter_message_lower_bounds = ros::Duration(0);
      vector_[i].warned_about_incorrect_bound = false;
    }
  }
  ApproximateTime(uint32_t queue_size, Callback callback, uint32_t id1, uint32_t id2, uint32_t id3, uint32_t id4)
: queue_size_(queue_size)
, callback_(callback)
, num_non_empty_deques_(0)
, pivot_(NO_PIVOT)
, max_interval_duration_(ros::DURATION_MAX)
, age_penalty_(0.1)
  {
    ROS_ASSERT(queue_size_ > 0);  // The synchronizer will tend to drop many messages with a queue size of 1. At least 2 is recommended.

    std::vector<unsigned int> ids(4);
    ids[0] = id1;
    ids[1] = id2;
    ids[2] = id3;
    ids[3] = id4;

    vector_.resize(ids.size());
    for (unsigned int i = 0; i < ids.size(); i++) {
      vector_[i].id = ids[i];
      vector_[i].has_dropped_messages = false;
      vector_[i].inter_message_lower_bounds = ros::Duration(0);
      vector_[i].warned_about_incorrect_bound = false;
    }
  }
  ApproximateTime(uint32_t queue_size, Callback callback, uint32_t id1, uint32_t id2, uint32_t id3, uint32_t id4, uint32_t id5)
: queue_size_(queue_size)
, callback_(callback)
, num_non_empty_deques_(0)
, pivot_(NO_PIVOT)
, max_interval_duration_(ros::DURATION_MAX)
, age_penalty_(0.1)
  {
    ROS_ASSERT(queue_size_ > 0);  // The synchronizer will tend to drop many messages with a queue size of 1. At least 2 is recommended.

    std::vector<unsigned int> ids(5);
    ids[0] = id1;
    ids[1] = id2;
    ids[2] = id3;
    ids[3] = id4;
    ids[4] = id5;

    vector_.resize(ids.size());
    for (unsigned int i = 0; i < ids.size(); i++) {
      vector_[i].id = ids[i];
      vector_[i].has_dropped_messages = false;
      vector_[i].inter_message_lower_bounds = ros::Duration(0);
      vector_[i].warned_about_incorrect_bound = false;
    }
  }
  ApproximateTime(uint32_t queue_size, Callback callback, uint32_t id1, uint32_t id2, uint32_t id3, uint32_t id4, uint32_t id5, uint32_t id6)
: queue_size_(queue_size)
, callback_(callback)
, num_non_empty_deques_(0)
, pivot_(NO_PIVOT)
, max_interval_duration_(ros::DURATION_MAX)
, age_penalty_(0.1)
  {
    ROS_ASSERT(queue_size_ > 0);  // The synchronizer will tend to drop many messages with a queue size of 1. At least 2 is recommended.

    std::vector<unsigned int> ids(6);
    ids[0] = id1;
    ids[1] = id2;
    ids[2] = id3;
    ids[3] = id4;
    ids[4] = id5;
    ids[5] = id6;

    vector_.resize(ids.size());
    for (unsigned int i = 0; i < ids.size(); i++) {
      vector_[i].id = ids[i];
      vector_[i].has_dropped_messages = false;
      vector_[i].inter_message_lower_bounds = ros::Duration(0);
      vector_[i].warned_about_incorrect_bound = false;
    }
  }
  ApproximateTime(uint32_t queue_size, Callback callback, uint32_t id1, uint32_t id2, uint32_t id3, uint32_t id4, uint32_t id5, uint32_t id6, uint32_t id7)
: queue_size_(queue_size)
, callback_(callback)
, num_non_empty_deques_(0)
, pivot_(NO_PIVOT)
, max_interval_duration_(ros::DURATION_MAX)
, age_penalty_(0.1)
  {
    ROS_ASSERT(queue_size_ > 0);  // The synchronizer will tend to drop many messages with a queue size of 1. At least 2 is recommended.

    std::vector<unsigned int> ids(7);
    ids[0] = id1;
    ids[1] = id2;
    ids[2] = id3;
    ids[3] = id4;
    ids[4] = id5;
    ids[5] = id6;
    ids[6] = id7;

    vector_.resize(ids.size());
    for (unsigned int i = 0; i < ids.size(); i++) {
      vector_[i].id = ids[i];
      vector_[i].has_dropped_messages = false;
      vector_[i].inter_message_lower_bounds = ros::Duration(0);
      vector_[i].warned_about_incorrect_bound = false;
    }
  }
  ApproximateTime(uint32_t queue_size, Callback callback, uint32_t id1, uint32_t id2, uint32_t id3, uint32_t id4, uint32_t id5, uint32_t id6, uint32_t id7, uint32_t id8)
: queue_size_(queue_size)
, callback_(callback)
, num_non_empty_deques_(0)
, pivot_(NO_PIVOT)
, max_interval_duration_(ros::DURATION_MAX)
, age_penalty_(0.1)
  {
    ROS_ASSERT(queue_size_ > 0);  // The synchronizer will tend to drop many messages with a queue size of 1. At least 2 is recommended.

    std::vector<unsigned int> ids(8);
    ids[0] = id1;
    ids[1] = id2;
    ids[2] = id3;
    ids[3] = id4;
    ids[4] = id5;
    ids[5] = id6;
    ids[6] = id7;
    ids[7] = id8;

    vector_.resize(ids.size());
    for (unsigned int i = 0; i < ids.size(); i++) {
      vector_[i].id = ids[i];
      vector_[i].has_dropped_messages = false;
      vector_[i].inter_message_lower_bounds = ros::Duration(0);
      vector_[i].warned_about_incorrect_bound = false;
    }
  }
  ApproximateTime(uint32_t queue_size, Callback callback, uint32_t id1, uint32_t id2, uint32_t id3, uint32_t id4, uint32_t id5, uint32_t id6, uint32_t id7, uint32_t id8, uint32_t id9)
: queue_size_(queue_size)
, callback_(callback)
, num_non_empty_deques_(0)
, pivot_(NO_PIVOT)
, max_interval_duration_(ros::DURATION_MAX)
, age_penalty_(0.1)
  {
    ROS_ASSERT(queue_size_ > 0);  // The synchronizer will tend to drop many messages with a queue size of 1. At least 2 is recommended.

    std::vector<unsigned int> ids(9);
    ids[0] = id1;
    ids[1] = id2;
    ids[2] = id3;
    ids[3] = id4;
    ids[4] = id5;
    ids[5] = id6;
    ids[6] = id7;
    ids[7] = id8;
    ids[8] = id9;

    vector_.resize(ids.size());
    for (unsigned int i = 0; i < ids.size(); i++) {
      vector_[i].id = ids[i];
      vector_[i].has_dropped_messages = false;
      vector_[i].inter_message_lower_bounds = ros::Duration(0);
      vector_[i].warned_about_incorrect_bound = false;
    }
  }
  ~ApproximateTime() {}

  void processMsg(const Type &msg)
  {
    for (unsigned int i = 0; i < vector_.size(); i++) {
      if (msg->msg.id == vector_[i].id) {
#if 0
        ROS_INFO("Id 0x%X: %u.%u", msg->msg.id, msg->header.stamp.sec, msg->header.stamp.nsec);
#endif
        std::deque<Type>& deque = vector_[i].deque;
        deque.push_back(msg);
        if (deque.size() == (size_t)1) {
          // We have just added the first message, so it was empty before
          ++num_non_empty_deques_;
          if (num_non_empty_deques_ == (uint32_t)vector_.size()) {
            // All deques have messages
            process();
          }
        } else {
          checkInterMessageBound(i);
        }

        // Check whether we have more messages than allowed in the queue.
        // Note that during the above call to process(), queue i may contain queue_size_+1 messages.
        std::vector<Type>& past = vector_[i].past;
        if (deque.size() + past.size() > queue_size_) {
          // Cancel ongoing candidate search, if any:
          num_non_empty_deques_ = 0; // We will recompute it from scratch
          {for (unsigned int i = 0; i < vector_.size(); i++) {
            recover(i);
          }}
          // Drop the oldest message in the offending topic
          ROS_ASSERT(!deque.empty());
          deque.pop_front();
          vector_[i].has_dropped_messages = true;
          if (pivot_ != NO_PIVOT) {
            // The candidate is no longer valid. Destroy it.
            for (unsigned int i = 0; i < vector_.size(); i++) {
              vector_[i].candidate.reset();
            }
            pivot_ = NO_PIVOT;
            // There might still be enough messages to create a new candidate:
            process();
          }
        }
        return;
      }
    }
  }


  void setAgePenalty(double age_penalty) {
    // For correctness we only need age_penalty > -1.0, but most likely a negative age_penalty is a mistake.
    ROS_ASSERT(age_penalty >= 0);
    age_penalty_ = age_penalty;
  }

  void setInterMessageLowerBound(unsigned int i, ros::Duration lower_bound) {
    // For correctness we only need age_penalty > -1.0, but most likely a negative age_penalty is a mistake.
    ROS_ASSERT(lower_bound >= ros::Duration(0,0));
    ROS_ASSERT((size_t)i < vector_.size());
    vector_[i].inter_message_lower_bounds = lower_bound;
  }

  void setMaxIntervalDuration(ros::Duration max_interval_duration) {
    // For correctness we only need age_penalty > -1.0, but most likely a negative age_penalty is a mistake.
    ROS_ASSERT(max_interval_duration >= ros::Duration(0,0));
    max_interval_duration_ = max_interval_duration;
  }


private:
  void checkInterMessageBound(unsigned int i)
  {
    namespace mt = ros::message_traits;
    if (vector_[i].warned_about_incorrect_bound) {
      return;
    }
    std::deque<Type>& deque = vector_[i].deque;
    std::vector<Type>& v = vector_[i].past;
    ROS_ASSERT(!deque.empty());
    ros::Time msg_time = deque.back()->header.stamp;
    ros::Time previous_msg_time;
    if (deque.size() == (size_t) 1) {
      if (v.empty()) {
        // We have already published (or have never received) the previous message, we cannot check the bound
        return;
      }
      previous_msg_time = v.back()->header.stamp;
    } else {
      // There are at least 2 elements in the deque. Check that the gap respects the bound if it was provided.
      previous_msg_time =  deque[deque.size()-2]->header.stamp;
    }
    if (msg_time < previous_msg_time) {
      ROS_WARN_STREAM("Messages of type " << i << " arrived out of order (will print only once)");
      vector_[i].warned_about_incorrect_bound = true;
    } else if ((msg_time - previous_msg_time) < vector_[i].inter_message_lower_bounds) {
      ROS_WARN_STREAM("Messages of type " << i << " arrived closer (" << (msg_time - previous_msg_time)
          << ") than the lower bound you provided (" << vector_[i].inter_message_lower_bounds
          << ") (will print only once)");
      vector_[i].warned_about_incorrect_bound = true;
    }
  }

  // Assumes that deque number <index> is non empty
  void dequeDeleteFront(unsigned int i)
  {
    std::deque<Type>& deque = vector_[i].deque;
    ROS_ASSERT(!deque.empty());
    deque.pop_front();
    if (deque.empty()) {
      --num_non_empty_deques_;
    }
  }

  // Assumes that deque number <index> is non empty
  void dequeMoveFrontToPast(unsigned int i)
  {
    std::deque<Type>& deque = vector_[i].deque;
    std::vector<Type>& vector = vector_[i].past;
    ROS_ASSERT(!deque.empty());
    vector.push_back(deque.front());
    deque.pop_front();
    if (deque.empty()) {
      --num_non_empty_deques_;
    }
  }

  void makeCandidate()
  {
    //printf("Creating candidate\n");
    for (unsigned int i = 0; i < vector_.size(); i++) {
      vector_[i].candidate = vector_[i].deque.front(); // Create candidate tuple
      vector_[i].past.clear(); // Delete all past messages, since we have found a better candidate
    }
    //printf("Candidate created\n");
  }

   void recover(unsigned int i, size_t num_messages)
   {
     std::vector<Type>& v = vector_[i].past;
     std::deque<Type>& q = vector_[i].deque;
     ROS_ASSERT(num_messages <= v.size());
     while (num_messages > 0) {
       q.push_front(v.back());
       v.pop_back();
       num_messages--;
     }

     if (!q.empty()) {
       ++num_non_empty_deques_;
     }
   }


   void recover(unsigned int i)
   {
     std::vector<Type>& v = vector_[i].past;
     std::deque<Type>& q = vector_[i].deque;
     while (!v.empty()) {
       q.push_front(v.back());
       v.pop_back();
     }

     if (!q.empty()) {
       ++num_non_empty_deques_;
     }
   }

   void recoverAndDelete(unsigned int i)
   {
     std::vector<Type>& v = vector_[i].past;
     std::deque<Type>& q = vector_[i].deque;
     while (!v.empty()) {
       q.push_front(v.back());
       v.pop_back();
     }

     ROS_ASSERT(!q.empty());

     q.pop_front();
     if (!q.empty()) {
       ++num_non_empty_deques_;
     }
   }

   // Assumes: all deques are non empty, i.e. num_non_empty_deques_ == RealTypeCount::value
   void publishCandidate()
   {
     //printf("Publishing candidate\n");
     // Publish
     std::vector<Type> candidate;
     for (unsigned int i = 0; i < vector_.size(); i++) {
       candidate.push_back(vector_[i].candidate);
     }
     callback_(candidate);

     // Delete this candidate
     for (unsigned int i = 0; i < vector_.size(); i++) {
       vector_[i].candidate.reset();
     }
     pivot_ = NO_PIVOT;

     // Recover hidden messages, and delete the ones corresponding to the candidate
     num_non_empty_deques_ = 0; // We will recompute it from scratch
     for (unsigned int i = 0; i < vector_.size(); i++) {
       recoverAndDelete(i);
     }
   }

   // Assumes: all deques are non empty, i.e. num_non_empty_deques_ == RealTypeCount::value
   // Returns: the oldest message on the deques
   void getCandidateStart(uint32_t &start_index, ros::Time &start_time)
   {
     return getCandidateBoundary(start_index, start_time, false);
   }

   // Assumes: all deques are non empty, i.e. num_non_empty_deques_ == RealTypeCount::value
   // Returns: the latest message among the heads of the deques, i.e. the minimum
   //          time to end an interval started at getCandidateStart_index()
   void getCandidateEnd(uint32_t &end_index, ros::Time &end_time)
   {
     return getCandidateBoundary(end_index, end_time, true);
   }

   // ASSUMES: all deques are non-empty
   // end = true: look for the latest head of deque
   //       false: look for the earliest head of deque
   void getCandidateBoundary(uint32_t &index, ros::Time &time, bool end)
   {
     time = vector_[0].deque.front()->header.stamp;
     index = 0;
     for (unsigned int i = 1; i < vector_.size(); i++) {
       const ros::Time &t = vector_[i].deque.front()->header.stamp;
       if ((t < time) ^ end) {
         time = t;
         index = i;
       }
     }
   }

   // ASSUMES: we have a pivot and candidate
   ros::Time getVirtualTime(unsigned int i)
   {
     namespace mt = ros::message_traits;

     if (i >= vector_.size()) {
       return ros::Time(0,0);  // Dummy return value
     }
     ROS_ASSERT(pivot_ != NO_PIVOT);

     std::vector<Type>& v = vector_[i].past;
     std::deque<Type>& q = vector_[i].deque;
     if (q.empty()) {
       ROS_ASSERT(!v.empty());  // Because we have a candidate
       ros::Time last_msg_time = v.back()->header.stamp;
       ros::Time msg_time_lower_bound = last_msg_time + vector_[i].inter_message_lower_bounds;
       if (msg_time_lower_bound > pivot_time_) { // Take the max
         return msg_time_lower_bound;
       }
       return pivot_time_;
     }
     ros::Time current_msg_time = q.front()->header.stamp;
     return current_msg_time;
   }


   // ASSUMES: we have a pivot and candidate
   void getVirtualCandidateStart(uint32_t &start_index, ros::Time &start_time)
   {
     return getVirtualCandidateBoundary(start_index, start_time, false);
   }

   // ASSUMES: we have a pivot and candidate
   void getVirtualCandidateEnd(uint32_t &end_index, ros::Time &end_time)
   {
     return getVirtualCandidateBoundary(end_index, end_time, true);
   }

   // ASSUMES: we have a pivot and candidate
   // end = true: look for the latest head of deque
   //       false: look for the earliest head of deque
   void getVirtualCandidateBoundary(uint32_t &index, ros::Time &time, bool end)
   {
     namespace mt = ros::message_traits;

     std::vector<ros::Time> virtual_times(vector_.size());
     for (unsigned int i = 0; i < vector_.size(); i++) {
       virtual_times[i] = getVirtualTime(i);
     }

     time = virtual_times[0];
     index = 0;
     for (unsigned int i = 0; i < vector_.size(); i++) {
       if ((virtual_times[i] < time) ^ end) {
         time = virtual_times[i];
         index = i;
       }
     }
   }


   // assumes data_mutex_ is already locked
   void process()
   {
     // While no deque is empty
     while (num_non_empty_deques_ == (uint32_t)vector_.size()) {
       // Find the start and end of the current interval
       //printf("Entering while loop in this state [\n");
       //show_internal_state();
       //printf("]\n");
       ros::Time end_time, start_time;
       uint32_t end_index, start_index;
       getCandidateEnd(end_index, end_time);
       getCandidateStart(start_index, start_time);
       for (uint32_t i = 0; i < (uint32_t)vector_.size(); i++) {
         if (i != end_index) {
           // No dropped message could have been better to use than the ones we have,
           // so it becomes ok to use this topic as pivot in the future
           vector_[i].has_dropped_messages = false;
         }
       }
       if (pivot_ == NO_PIVOT) {
         // We do not have a candidate
         // INVARIANT: the past_ vectors are empty
         // INVARIANT: (candidate_ has no filled members)
         if (end_time - start_time > max_interval_duration_) {
           // This interval is too big to be a valid candidate, move to the next
           dequeDeleteFront(start_index);
           continue;
         }
         if (vector_[end_index].has_dropped_messages) {
           // The topic that would become pivot has dropped messages, so it is not a good pivot
           dequeDeleteFront(start_index);
           continue;
         }
         // This is a valid candidate, and we don't have any, so take it
         makeCandidate();
         candidate_start_ = start_time;
         candidate_end_ = end_time;
         pivot_ = end_index;
         pivot_time_ = end_time;
         dequeMoveFrontToPast(start_index);
       } else {
         // We already have a candidate
         // Is this one better than the current candidate?
         // INVARIANT: has_dropped_messages_ is all false
         if ((end_time - candidate_end_) * (1 + age_penalty_) >= (start_time - candidate_start_)) {
           // This is not a better candidate, move to the next
           dequeMoveFrontToPast(start_index);
         } else {
           // This is a better candidate
           makeCandidate();
           candidate_start_ = start_time;
           candidate_end_ = end_time;
           dequeMoveFrontToPast(start_index);
           // Keep the same pivot (and pivot time)
         }
       }
       // INVARIANT: we have a candidate and pivot
       ROS_ASSERT(pivot_ != NO_PIVOT);
       //printf("start_index == %d, pivot_ == %d\n", start_index, pivot_);
       if (start_index == pivot_) { // TODO: replace with start_time == pivot_time_
         // We have exhausted all possible candidates for this pivot, we now can output the best one
         publishCandidate();
       } else if ((end_time - candidate_end_) * (1 + age_penalty_) >= (pivot_time_ - candidate_start_)) {
         // We have not exhausted all candidates, but this candidate is already provably optimal
         // Indeed, any future candidate must contain the interval [pivot_time_ end_time], which
         // is already too big.
         // Note: this case is subsumed by the next, but it may save some unnecessary work and
         //       it makes things (a little) easier to understand
         publishCandidate();
       } else if (num_non_empty_deques_ < (uint32_t)vector_.size()) {
         uint32_t num_non_empty_deques_before_virtual_search = num_non_empty_deques_;

         // Before giving up, use the rate bounds, if provided, to further try to prove optimality
         std::vector<int> num_virtual_moves(9,0);
         while (1) {
           ros::Time end_time, start_time;
           uint32_t end_index, start_index;
           getVirtualCandidateEnd(end_index, end_time);
           getVirtualCandidateStart(start_index, start_time);
           if ((end_time - candidate_end_) * (1 + age_penalty_) >= (pivot_time_ - candidate_start_)) {
             // We have proved optimality
             // As above, any future candidate must contain the interval [pivot_time_ end_time], which
             // is already too big.
             publishCandidate();  // This cleans up the virtual moves as a byproduct
             break;  // From the while(1) loop only
           }
           if ((end_time - candidate_end_) * (1 + age_penalty_) < (start_time - candidate_start_)) {
             // We cannot prove optimality
             // Indeed, we have a virtual (i.e. optimistic) candidate that is better than the current
             // candidate
             // Cleanup the virtual search:
             num_non_empty_deques_ = 0; // We will recompute it from scratch
             for (unsigned int i = 0; i < vector_.size(); i++) {
               recover(i, num_virtual_moves[i]);
             }
             (void)num_non_empty_deques_before_virtual_search; // unused variable warning stopper
             ROS_ASSERT(num_non_empty_deques_before_virtual_search == num_non_empty_deques_);
             break;
           }
           // Note: we cannot reach this point with start_index == pivot_ since in that case we would
           //       have start_time == pivot_time, in which case the two tests above are the negation
           //       of each other, so that one must be true. Therefore the while loop always terminates.
           ROS_ASSERT(start_index != pivot_);
           ROS_ASSERT(start_time < pivot_time_);
           dequeMoveFrontToPast(start_index);
           num_virtual_moves[start_index]++;
         } // while(1)
       }
     } // while(num_non_empty_deques_ == (uint32_t)RealTypeCount::value)
   }


  uint32_t queue_size_;
  Callback callback_;

  static const uint32_t NO_PIVOT = 9;  // Special value for the pivot indicating that no pivot has been selected

  typedef struct {
    uint32_t id;
    std::deque<Type> deque;
    std::vector<Type> past;
    Type candidate;  // NULL if there is no candidate, in which case there is no pivot.
    bool has_dropped_messages;
    ros::Duration inter_message_lower_bounds;
    bool warned_about_incorrect_bound;
  } VectorData;
  std::vector<VectorData> vector_;
  uint32_t num_non_empty_deques_;
  ros::Time candidate_start_;
  ros::Time candidate_end_;
  ros::Time pivot_time_;
  uint32_t pivot_;  // Equal to NO_PIVOT if there is no candidate

  ros::Duration max_interval_duration_; // TODO: initialize with a parameter
  double age_penalty_;
};

} // namespace dataspeed_can_msg_filters

#endif // _CAN_APPROXIMATE_TIME_H_
