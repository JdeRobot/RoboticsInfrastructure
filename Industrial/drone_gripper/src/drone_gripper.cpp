// Drone magnetic gripper system plugin for gz-sim (Harmonic).
//
// Behaves like an electromagnet: while energized it attaches the nearest
// graspable model within a configurable distance to the gripper link using a
// physical DetachableJoint, and releases it when de-energized. It is driven
// through ROS2 topics so the same interface works for Python and C++ user code.
//
// SDF parameters (all optional):
//   <gripper_model>    model that carries the magnet         (default: drone0)
//   <gripper_link>     link the payload is attached to       (default: base_link)
//   <graspable_models> comma separated model names to grab   (default: "")
//   <attach_distance>  max distance to grab a payload, in m  (default: 1.0)
//   <magnet_topic>     std_msgs/Bool, energize/de-energize   (default: /drone0/gripper/magnet)
//   <state_topic>      std_msgs/Bool, currently carrying?    (default: /drone0/gripper/attached)

#include <gz/sim/System.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/Model.hh>

#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/DetachableJoint.hh>

#include <gz/plugin/Register.hh>
#include <gz/math/Pose3.hh>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/bool.hpp>

#include <thread>
#include <mutex>
#include <chrono>
#include <vector>
#include <sstream>
#include <string>
#include <algorithm>
#include <cctype>
#include <iostream>

using namespace gz;
using namespace sim;

namespace drone_gripper
{

class DroneGripper :
  public System,
  public ISystemConfigure,
  public ISystemPreUpdate
{

public:

DroneGripper() = default;

~DroneGripper()
{
  if (this->executor)
    this->executor->cancel();

  if (this->rosThread.joinable())
    this->rosThread.join();
}

void Configure(
  const Entity &,
  const std::shared_ptr<const sdf::Element> &_sdf,
  EntityComponentManager &,
  EventManager &) override
{
  this->gripperModelName = _sdf->Get<std::string>("gripper_model", "drone0").first;
  this->gripperLinkName  = _sdf->Get<std::string>("gripper_link", "base_link").first;
  this->attachDistance   = _sdf->Get<double>("attach_distance", 1.0).first;

  const std::string graspable = _sdf->Get<std::string>("graspable_models", "").first;
  std::stringstream ss(graspable);
  std::string item;
  while (std::getline(ss, item, ','))
  {
    item.erase(std::remove_if(item.begin(), item.end(), ::isspace), item.end());
    if (!item.empty())
      this->graspableModels.push_back(item);
  }

  const std::string magnetTopic = _sdf->Get<std::string>("magnet_topic", "/drone0/gripper/magnet").first;
  const std::string stateTopic  = _sdf->Get<std::string>("state_topic", "/drone0/gripper/attached").first;

  if (!rclcpp::ok())
  {
    int argc = 0;
    char **argv = nullptr;
    rclcpp::init(argc, argv);
  }

  this->node = std::make_shared<rclcpp::Node>("drone_gripper");
  this->executor = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
  this->executor->add_node(this->node);

  this->magnetSub = this->node->create_subscription<std_msgs::msg::Bool>(
    magnetTopic, 10,
    [this](const std_msgs::msg::Bool::SharedPtr msg)
    {
      std::lock_guard<std::mutex> lock(this->mutex);
      this->magnetEnabled = msg->data;
    });

  this->statePub = this->node->create_publisher<std_msgs::msg::Bool>(stateTopic, 10);

  this->rosThread = std::thread([this]()
  {
    while (rclcpp::ok())
    {
      this->executor->spin_some();
      std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
  });

  std::cout << "[DroneGripper] Configured: " << this->gripperModelName
            << "::" << this->gripperLinkName
            << " attach_distance=" << this->attachDistance << std::endl;
}

void PreUpdate(
  const UpdateInfo &_info,
  EntityComponentManager &_ecm) override
{
  if (_info.paused)
    return;

  bool enabled;
  {
    std::lock_guard<std::mutex> lock(this->mutex);
    enabled = this->magnetEnabled;
  }

  if (enabled && this->activeJoint == kNullEntity)
    this->TryAttach(_ecm);
  else if (!enabled && this->activeJoint != kNullEntity)
    this->Detach(_ecm);

  // Publish carrying state at ~10 Hz.
  if (++this->publishCounter >= 25)
  {
    this->publishCounter = 0;
    std_msgs::msg::Bool m;
    m.data = (this->activeJoint != kNullEntity);
    this->statePub->publish(m);
  }
}

private:

Entity FindModel(EntityComponentManager &_ecm, const std::string &modelName)
{
  return _ecm.EntityByComponents(components::Name(modelName), components::Model());
}

Entity FindLink(
  EntityComponentManager &_ecm,
  const std::string &modelName,
  const std::string &linkName)
{
  const Entity modelEntity = this->FindModel(_ecm, modelName);
  if (modelEntity == kNullEntity)
    return kNullEntity;

  Entity result{kNullEntity};
  _ecm.Each<components::Name, components::ParentEntity>(
    [&](const Entity &_entity,
        const components::Name *_name,
        const components::ParentEntity *_parent)
    {
      if (_name->Data() == linkName && _parent->Data() == modelEntity)
      {
        result = _entity;
        return false;
      }
      return true;
    });

  return result;
}

// Energized magnet: attach the closest graspable model within range.
void TryAttach(EntityComponentManager &_ecm)
{
  const Entity gripperLink =
    this->FindLink(_ecm, this->gripperModelName, this->gripperLinkName);
  if (gripperLink == kNullEntity)
    return;

  const math::Pose3d gripperPose = worldPose(gripperLink, _ecm);

  Entity bestChild = kNullEntity;
  double bestDist = this->attachDistance;

  for (const auto &name : this->graspableModels)
  {
    const Entity modelEntity = this->FindModel(_ecm, name);
    if (modelEntity == kNullEntity)
      continue;

    const Entity childLink = Model(modelEntity).CanonicalLink(_ecm);
    if (childLink == kNullEntity)
      continue;

    const math::Pose3d childPose = worldPose(childLink, _ecm);
    const double dist = (gripperPose.Pos() - childPose.Pos()).Length();
    if (dist <= bestDist)
    {
      bestDist = dist;
      bestChild = childLink;
    }
  }

  if (bestChild == kNullEntity)
    return;

  const Entity jointEntity = _ecm.CreateEntity();
  components::DetachableJoint joint;
  joint.Data().parentLink = gripperLink;
  joint.Data().childLink  = bestChild;
  joint.Data().jointType  = "fixed";
  _ecm.CreateComponent(jointEntity, joint);

  this->activeJoint = jointEntity;
  std::cout << "[DroneGripper] Attached payload (dist=" << bestDist << ")" << std::endl;
}

void Detach(EntityComponentManager &_ecm)
{
  if (this->activeJoint == kNullEntity)
    return;

  _ecm.RequestRemoveEntity(this->activeJoint);
  this->activeJoint = kNullEntity;
  std::cout << "[DroneGripper] Released payload" << std::endl;
}

private:

rclcpp::Node::SharedPtr node;
rclcpp::executors::SingleThreadedExecutor::SharedPtr executor;
rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr magnetSub;
rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr statePub;
std::thread rosThread;

std::string gripperModelName;
std::string gripperLinkName;
std::vector<std::string> graspableModels;
double attachDistance{1.0};

std::mutex mutex;
bool magnetEnabled{false};
Entity activeJoint{kNullEntity};
int publishCounter{0};

};

}

GZ_ADD_PLUGIN(
  drone_gripper::DroneGripper,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)
