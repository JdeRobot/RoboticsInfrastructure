// Drone magnetic gripper system plugin for gz-sim (Harmonic).
//
// This is a MODEL plugin: it is attached to the drone in its own SDF/URDF, so
// it knows which robot it belongs to (no hard-coded model name) and works with
// renamed models and several drones at once. It behaves like an electromagnet:
// while energized it attaches the nearest graspable model within a configurable
// distance to the gripper link with a physical DetachableJoint, and releases it
// when de-energized. It is driven through ROS2 topics, so the same interface
// works for Python and C++ user code.
//
// The graspable models are NOT baked into the robot: the exercise publishes
// them on the graspable topic, keeping the robot independent of any world.
//
// SDF parameters (all optional):
//   <gripper_link>     link the payload is attached to      (default: base_link)
//   <attach_distance>  max distance to grab a payload, in m (default: 0.15)
//   <magnet_topic>     std_msgs/Bool, energize/de-energize  (default: /<model>/gripper/magnet)
//   <state_topic>      std_msgs/Bool, currently carrying?   (default: /<model>/gripper/attached)
//   <graspable_topic>  std_msgs/String, CSV grabbable names (default: /<model>/gripper/graspable)

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
#include <std_msgs/msg/string.hpp>

#include <thread>
#include <mutex>
#include <atomic>
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
  public ISystemPreUpdate,
  public ISystemReset
{

public:

DroneGripper() = default;

~DroneGripper()
{
  // Stop the ROS thread first. As a MODEL plugin this destructor runs every
  // time the drone is removed (e.g. on reset), so it must return promptly; a
  // hanging join would wedge gz and stop the drone re-spawning.
  this->running_ = false;

  if (this->executor)
    this->executor->cancel();

  if (this->rosThread.joinable())
    this->rosThread.join();
}

void Configure(
  const Entity &_entity,
  const std::shared_ptr<const sdf::Element> &_sdf,
  EntityComponentManager &_ecm,
  EventManager &) override
{
  // Model plugin: _entity is the drone model that carries the magnet.
  this->modelEntity = _entity;

  auto nameComp = _ecm.Component<components::Name>(_entity);
  const std::string modelName = nameComp ? nameComp->Data() : "drone";

  this->gripperLinkName = _sdf->Get<std::string>("gripper_link", "base_link").first;
  this->attachDistance  = _sdf->Get<double>("attach_distance", 0.15).first;

  const std::string ns = "/" + modelName + "/gripper";
  const std::string magnetTopic    = _sdf->Get<std::string>("magnet_topic", ns + "/magnet").first;
  const std::string stateTopic     = _sdf->Get<std::string>("state_topic", ns + "/attached").first;
  const std::string graspableTopic = _sdf->Get<std::string>("graspable_topic", ns + "/graspable").first;

  if (!rclcpp::ok())
  {
    int argc = 0;
    char **argv = nullptr;
    rclcpp::init(argc, argv);
  }

  this->node = std::make_shared<rclcpp::Node>("drone_gripper_" + modelName);
  this->executor = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
  this->executor->add_node(this->node);

  this->magnetSub = this->node->create_subscription<std_msgs::msg::Bool>(
    magnetTopic, 10,
    [this](const std_msgs::msg::Bool::SharedPtr msg)
    {
      std::lock_guard<std::mutex> lock(this->mutex);
      this->magnetEnabled = msg->data;
    });

  // The exercise defines what can be grabbed, so the robot stays independent
  // of any world/object. Latched QoS so a list published once is not missed.
  rclcpp::QoS graspableQos(10);
  graspableQos.transient_local();
  this->graspableSub = this->node->create_subscription<std_msgs::msg::String>(
    graspableTopic, graspableQos,
    [this](const std_msgs::msg::String::SharedPtr msg)
    {
      std::lock_guard<std::mutex> lock(this->mutex);
      this->graspableModels.clear();
      std::stringstream ss(msg->data);
      std::string item;
      while (std::getline(ss, item, ','))
      {
        item.erase(std::remove_if(item.begin(), item.end(), ::isspace), item.end());
        if (!item.empty())
          this->graspableModels.push_back(item);
      }
    });

  this->statePub = this->node->create_publisher<std_msgs::msg::Bool>(stateTopic, 10);

  this->rosThread = std::thread([this]()
  {
    while (this->running_ && rclcpp::ok())
    {
      this->executor->spin_some();
      std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
    // Tear down our ROS node from this thread (no race with spinning) so a
    // plugin instance whose model was removed on reset does not linger as a
    // zombie with a duplicate node name that corrupts the ROS graph.
    if (this->executor && this->node)
      this->executor->remove_node(this->node);
    this->statePub.reset();
    this->magnetSub.reset();
    this->graspableSub.reset();
    this->node.reset();
  });

  std::cout << "[DroneGripper] Configured on model " << modelName
            << " link=" << this->gripperLinkName
            << " attach_distance=" << this->attachDistance << std::endl;
}

void PreUpdate(
  const UpdateInfo &_info,
  EntityComponentManager &_ecm) override
{
  // Already shut down (our model was removed on reset): do nothing.
  if (this->dead_)
    return;

  // Our own model was removed (e.g. reset removed the drone). Release the box
  // and shut ourselves down: stop the ROS thread so this instance stops being
  // a zombie with a duplicate node name. gz recreates a fresh plugin for the
  // re-spawned drone.
  if (!_ecm.HasEntity(this->modelEntity))
  {
    if (this->activeJoint != kNullEntity)
    {
      _ecm.RequestRemoveEntity(this->activeJoint);
      this->activeJoint = kNullEntity;
    }
    this->running_ = false;
    this->dead_ = true;
    return;
  }

  // Drop the joint if the drone is gone OR is being removed this very cycle.
  // Reset removes the drone first; detaching in the SAME cycle as the removal
  // keeps the DetachableJoint from outliving the drone links, which would wedge
  // the physics server and stop the drone re-spawning. Runs even while paused,
  // because reset happens with the world paused.
  //TODO: review
  if (this->activeJoint != kNullEntity && this->GripperGoneOrRemoving(_ecm))
  {
    this->HandleResetDetach(_ecm);
  }

  if (_info.paused)
  {
    // TODO: commented because it detaches when the user presses pause
    // A reset pauses the world before removing/resetting the drone. Detach the
    // box (so it is not jointed to the drone when it is removed) AND de-energize
    // the magnet. De-energizing is key: otherwise TryAttach would auto-re-attach
    // on unpause, leaving the gripper stuck "carrying" a stale/reset box so it
    // never grabs again. The exercise re-energizes the magnet when it wants to
    // grab, so a fresh run works normally. If GripperGoneOrRemoving already
    // handled it above this cycle, activeJoint is already null here.
    // if (this->activeJoint != kNullEntity)
    //   this->HandleResetDetach(_ecm);
    // {
    //   std::lock_guard<std::mutex> lock(this->mutex);
    //   this->magnetEnabled = false;
    // }
    return;
  }

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

// Called on world reset: drop any joint and clear state so nothing references
// the drone that reset removes and re-creates.
void Reset(
  const UpdateInfo &,
  EntityComponentManager &_ecm) override
{
  if (this->activeJoint != kNullEntity)
  {
    _ecm.RequestRemoveEntity(this->activeJoint);
    this->activeJoint = kNullEntity;
  }
  this->carriedModel = kNullEntity;

  std::lock_guard<std::mutex> lock(this->mutex);
  this->magnetEnabled = false;
  this->publishCounter = 0;
}

private:

// Detach because reset is tearing things down (drone removal or world pause),
// as opposed to a normal exercise-triggered disable_magnet(). Announces the
// release immediately: the periodic heartbeat below never gets there, since
// this instance is about to die, so without this HAL's cached "carrying"
// state stays stale (true) until the respawned drone's fresh plugin instance
// publishes its first heartbeat.
//
// NOTE: this used to also RequestRemoveEntity() the payload model itself, to
// work around a DetachableJoint that silently stops enforcing on a link that
// was jointed once before. That was reverted - removing a model entity
// during the paused/reset transition looks like the cause of gzserver dying
// after repeated carry-then-reset cycles. The stale-physics bug is still
// open; needs a safer fix.
void HandleResetDetach(EntityComponentManager &_ecm)
{
  this->Detach(_ecm);

  std_msgs::msg::Bool m;
  m.data = false;
  this->statePub->publish(m);
}

Entity FindModel(EntityComponentManager &_ecm, const std::string &modelName)
{
  return _ecm.EntityByComponents(components::Name(modelName), components::Model());
}

// True if our own drone model no longer exists, or is marked for removal in the
// current update cycle (EachRemoved reports entities erased at cycle end).
bool GripperGoneOrRemoving(EntityComponentManager &_ecm)
{
  if (!_ecm.HasEntity(this->modelEntity))
    return true;

  bool removing = false;
  _ecm.EachRemoved<components::Model>(
    [&](const Entity &_e, const components::Model *)
    {
      if (_e == this->modelEntity)
        removing = true;
      return true;
    });
  return removing;
}

// Find a link by name inside a given model.
Entity FindLinkInModel(
  EntityComponentManager &_ecm,
  Entity model,
  const std::string &linkName)
{
  Entity result{kNullEntity};
  _ecm.Each<components::Name, components::ParentEntity>(
    [&](const Entity &_entity,
        const components::Name *_name,
        const components::ParentEntity *_parent)
    {
      if (_name->Data() == linkName && _parent->Data() == model)
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
    this->FindLinkInModel(_ecm, this->modelEntity, this->gripperLinkName);
  if (gripperLink == kNullEntity)
    return;

  std::vector<std::string> graspables;
  {
    std::lock_guard<std::mutex> lock(this->mutex);
    graspables = this->graspableModels;
  }
  if (graspables.empty())
    return;

  const math::Pose3d gripperPose = worldPose(gripperLink, _ecm);

  Entity bestChild = kNullEntity;
  Entity bestModel = kNullEntity;
  double bestDist = this->attachDistance;

  for (const auto &name : graspables)
  {
    const Entity candidateModel = this->FindModel(_ecm, name);
    if (candidateModel == kNullEntity)
      continue;

    const Entity childLink = Model(candidateModel).CanonicalLink(_ecm);
    if (childLink == kNullEntity)
      continue;

    const math::Pose3d childPose = worldPose(childLink, _ecm);
    const double dist = (gripperPose.Pos() - childPose.Pos()).Length();
    if (dist <= bestDist)
    {
      bestDist = dist;
      bestChild = childLink;
      bestModel = candidateModel;
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
  this->carriedModel = bestModel;
  std::cout << "[DroneGripper] Attached payload (dist=" << bestDist << ")" << std::endl;
}

void Detach(EntityComponentManager &_ecm)
{
  if (this->activeJoint == kNullEntity)
    return;

  _ecm.RequestRemoveEntity(this->activeJoint);
  this->activeJoint = kNullEntity;
  this->carriedModel = kNullEntity;
  std::cout << "[DroneGripper] Released payload" << std::endl;
}

private:

rclcpp::Node::SharedPtr node;
rclcpp::executors::SingleThreadedExecutor::SharedPtr executor;
rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr magnetSub;
rclcpp::Subscription<std_msgs::msg::String>::SharedPtr graspableSub;
rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr statePub;
std::thread rosThread;
std::atomic<bool> running_{true};
bool dead_{false};

Entity modelEntity{kNullEntity};
std::string gripperLinkName;
std::vector<std::string> graspableModels;
double attachDistance{0.15};

std::mutex mutex;
bool magnetEnabled{false};
Entity activeJoint{kNullEntity};
Entity carriedModel{kNullEntity};
int publishCounter{0};

};

}

GZ_ADD_PLUGIN(
  drone_gripper::DroneGripper,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate,
  gz::sim::ISystemReset
)