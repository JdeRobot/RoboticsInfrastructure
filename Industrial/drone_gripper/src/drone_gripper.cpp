// Drone magnetic gripper system plugin for gz-sim (Harmonic).
// Fix: flush entity removals after requesting joint removal to avoid
// reparented body corruption on reset.
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
    running_ = false;
    if (executor)
      executor->cancel();
    if (rosThread.joinable())
      rosThread.join();
  }

  void Configure(
    const Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    EntityComponentManager &_ecm,
    EventManager &) override
  {
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
    if (this->dead_)
      return;

    if (!_ecm.HasEntity(this->modelEntity))
    {
      if (this->activeJoint != kNullEntity)
        this->Detach(_ecm);
      this->running_ = false;
      this->dead_ = true;
      return;
    }

    if (this->pendingJoint != kNullEntity)
    {
      if (_ecm.HasEntity(this->pendingJoint))
        return;
      this->pendingJoint = kNullEntity;
    }

    if (this->activeJoint != kNullEntity && this->GripperGoneOrRemoving(_ecm))
    {
      this->HandleResetDetach(_ecm);
    }

    if (_info.paused)
    {
      if (this->activeJoint != kNullEntity)
        this->HandleResetDetach(_ecm);
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

    if (++this->publishCounter >= 25)
    {
      this->publishCounter = 0;
      std_msgs::msg::Bool m;
      m.data = (this->activeJoint != kNullEntity);
      this->statePub->publish(m);
    }
  }

  void Reset(
    const UpdateInfo &,
    EntityComponentManager &_ecm) override
  {
    if (this->activeJoint != kNullEntity)
    {
      this->Detach(_ecm);
    }
    this->carriedModel = kNullEntity;

    std::lock_guard<std::mutex> lock(this->mutex);
    this->magnetEnabled = false;
    this->publishCounter = 0;
  }

private:
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

    if (this->pendingJoint != kNullEntity)
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

    if (_ecm.HasEntity(this->activeJoint))
    {
      this->pendingJoint = this->activeJoint;
      _ecm.RequestRemoveEntity(this->activeJoint);
      _ecm.ProcessRemoveEntityRequests();
    }
    this->activeJoint = kNullEntity;
    this->carriedModel = kNullEntity;
    std::cout << "[DroneGripper] Released payload" << std::endl;
  }

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
  Entity pendingJoint{kNullEntity};
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
