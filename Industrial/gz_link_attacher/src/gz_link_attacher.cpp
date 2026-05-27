#include <gz/sim/System.hh>

#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/DetachableJoint.hh>
#include <gz/sim/components/ContactSensorData.hh>

#include <gz/plugin/Register.hh>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/bool.hpp>

#include <thread>
#include <chrono>
#include <iostream>

using namespace gz;
using namespace sim;

namespace gz_link_attacher
{

class LinkAttacher :
  public System,
  public ISystemConfigure,
  public ISystemPreUpdate
{

public:

LinkAttacher()
{
  std::cout << "\n==============================" << std::endl;
  std::cout << "[LinkAttacher] Constructor called" << std::endl;
  std::cout << "==============================\n" << std::endl;
}

~LinkAttacher()
{
  std::cout << "[LinkAttacher] Destructor called" << std::endl;

  if (executor)
  {
    std::cout << "[LinkAttacher] Stopping executor" << std::endl;
    executor->cancel();
  }

  if (rosThread.joinable())
  {
    std::cout << "[LinkAttacher] Joining ROS thread" << std::endl;
    rosThread.join();
  }
}

void Configure(
  const Entity &_entity,
  const std::shared_ptr<const sdf::Element> &,
  EntityComponentManager &,
  EventManager &) override
{

  std::cout << "\n[LinkAttacher] Configure() START\n";

  worldEntity = _entity;

  std::cout << "[LinkAttacher] World entity: " << worldEntity << std::endl;

  if (!rclcpp::ok())
  {
    std::cout << "[LinkAttacher] Initializing ROS2..." << std::endl;

    int argc = 0;
    char **argv = nullptr;
    rclcpp::init(argc, argv);
  }

  std::cout << "[LinkAttacher] Creating ROS node" << std::endl;

  node = std::make_shared<rclcpp::Node>("gz_link_attacher");

  std::cout << "[LinkAttacher] Node created: " << node->get_name() << std::endl;

  executor = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();

  std::cout << "[LinkAttacher] Adding node to executor" << std::endl;

  executor->add_node(node);

  gripperStateSub =
  node->create_subscription<std_msgs::msg::Bool>(
    "/gripper_auto_attach",
    10,
    [this](const std_msgs::msg::Bool::SharedPtr msg)
    {
      autoAttachEnabled = msg->data;

      if (!autoAttachEnabled)
      {
        contactLatched = false;

        if (activeJoint != kNullEntity)
        {
          removeJointRequested = true;
        }
      }
    });

  std::cout << "[LinkAttacher] Starting ROS thread" << std::endl;

  rosThread = std::thread([this]()
  {
    std::cout << "[LinkAttacher] ROS thread started" << std::endl;

    while (rclcpp::ok())
    {
      executor->spin_some();

      std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    std::cout << "[LinkAttacher] ROS thread exiting" << std::endl;
  });

  std::cout << "[LinkAttacher] Configure() END\n" << std::endl;
}

void PreUpdate(
  const UpdateInfo &,
  EntityComponentManager &_ecm) override
{

  if(!initialized)
  {
    std::cout << "[LinkAttacher] First PreUpdate() detected" << std::endl;
    initialized = true;
  }

  CheckGripperContact(_ecm);

  if (createJointRequested)
  {
    std::cout
      << "[LinkAttacher] Executing CreateJoint()"
      << std::endl;

    CreateJoint(_ecm);
    createJointRequested = false;
  }

  if (removeJointRequested)
  {
    RemoveJoint(_ecm);
    removeJointRequested = false;
  }
}

private:

bool IsFingerTip(
  EntityComponentManager &_ecm,
  Entity collisionEntity)
{
  auto parentComp =
    _ecm.Component<components::ParentEntity>(
      collisionEntity);

  if (!parentComp)
    return false;

  Entity linkEntity =
    parentComp->Data();

  auto nameComp =
    _ecm.Component<components::Name>(
      linkEntity);

  if (!nameComp)
    return false;

  const std::string &name =
    nameComp->Data();

  std::cout
    << "[LinkAttacher] Checking finger link: "
    << name
    << std::endl;

  return (
    name.find("finger") != std::string::npos
  );
}

std::string GetModelNameFromCollision(
  EntityComponentManager &_ecm,
  Entity collisionEntity)
{
  auto collisionParent =
    _ecm.Component<components::ParentEntity>(
      collisionEntity);

  if (!collisionParent)
    return "";

  Entity linkEntity =
    collisionParent->Data();

  auto linkParent =
    _ecm.Component<components::ParentEntity>(
      linkEntity);

  if (!linkParent)
    return "";

  Entity modelEntity =
    linkParent->Data();

  auto nameComp =
    _ecm.Component<components::Name>(
      modelEntity);

  if (!nameComp)
    return "";

  return nameComp->Data();
}

std::string GetLinkNameFromCollision(
  EntityComponentManager &_ecm,
  Entity collisionEntity)
{
  auto parentComp =
    _ecm.Component<components::ParentEntity>(
      collisionEntity);

  if (!parentComp)
    return "";

  Entity linkEntity =
    parentComp->Data();

  auto nameComp =
    _ecm.Component<components::Name>(
      linkEntity);

  if (!nameComp)
    return "";

  return nameComp->Data();
}

void CheckGripperContact(
  EntityComponentManager &_ecm)
{
  std::cout << "[LinkAttacher] CheckGripperContact()" << std::endl;

  if (!autoAttachEnabled)
    std::cout << "[LinkAttacher] autoAttach disabled" << std::endl;
    return;

  if (contactLatched)
    return;

  if (activeJoint != kNullEntity)
    return;

  if (createJointRequested)
    return;

  std::cout
    << "[LinkAttacher] Searching ContactSensorData..."
    << std::endl;

  _ecm.Each<components::ContactSensorData>(
    [&](const Entity &,
        const components::ContactSensorData *_contacts)
    {
      if (!_contacts)
        return true;

      const auto &msgs =
        _contacts->Data().contact();

      std::cout
        << "[LinkAttacher] contacts size = "
        << msgs.size()
        << std::endl;

      for (const auto &contact : msgs)
      {
        Entity collision1 =
          contact.collision1().id();

        Entity collision2 =
          contact.collision2().id();

        std::string linkName1 =
          GetLinkNameFromCollision(_ecm, collision1);

        std::string linkName2 =
          GetLinkNameFromCollision(_ecm, collision2);

        std::cout
          << "[LinkAttacher] collision1="
          << collision1
          << " collision2="
          << collision2
          << std::endl;

        bool finger1 =
          IsFingerTip(_ecm, collision1);

        bool finger2 =
          IsFingerTip(_ecm, collision2);

        if (!finger1 && !finger2)
          continue;

        Entity objectCollision =
          finger1 ? collision2 : collision1;

        std::string objectModel =
          GetModelNameFromCollision(
            _ecm,
            objectCollision);

        std::cout
          << "[LinkAttacher] objectModel="
          << objectModel
          << std::endl;

        if (
          objectModel.empty() ||
          objectModel == "ur5_robotiq"
        )
        {
          continue;
        }

        if (
          objectModel == "ground_plane" ||
          objectModel == "sun"
        )
        {
          continue;
        }

        std::cout
          << "[LinkAttacher] Contact with object: "
          << objectModel
          << std::endl;

        model1 = "ur5_robotiq";
        link1 = "robotiq_85_base_link";

        model2 = objectModel;

        if (objectModel == "blue_ball")
          link2 = "link_3";
        else if (objectModel == "green_cylinder")
          link2 = "link_2";
        else
          link2 = "link";

        std::cout
          << "[LinkAttacher] Requesting joint creation"
          << std::endl;

        createJointRequested = true;
        contactLatched = true;

        return false;
      }

      return true;
    });
}

Entity FindLink(
  EntityComponentManager &_ecm,
  const std::string &modelName,
  const std::string &linkName)
{

  std::cout << "[LinkAttacher] Searching model: " << modelName << std::endl;

  Entity modelEntity{kNullEntity};

  _ecm.Each<components::Name>(
    [&](const Entity &_entity,const components::Name *_name)
    {

      if(_name->Data()==modelName)
      {
        std::cout << "[LinkAttacher] Model found entity=" << _entity << std::endl;
        modelEntity=_entity;
        return false;
      }

      return true;

    });

  if(modelEntity==kNullEntity)
  {
    std::cout<<"[LinkAttacher] MODEL NOT FOUND: "<<modelName<<std::endl;
    return kNullEntity;
  }

  std::cout << "[LinkAttacher] Searching link: " << linkName << std::endl;

  Entity result{kNullEntity};

  _ecm.Each<components::Name,components::ParentEntity>(
    [&](const Entity &_entity,
        const components::Name *_name,
        const components::ParentEntity *_parent)
    {

      if(_name->Data()==linkName && _parent->Data()==modelEntity)
      {
        std::cout << "[LinkAttacher] Link found entity=" << _entity << std::endl;
        result=_entity;
        return false;
      }

      return true;

    });

  if(result==kNullEntity)
  {
    std::cout<<"[LinkAttacher] LINK NOT FOUND: "
             <<modelName<<"::"<<linkName<<std::endl;
  }

  return result;
}

void CreateJoint(EntityComponentManager &_ecm)
{
  if (activeJoint != kNullEntity)
  {
    std::cout
      << "[LinkAttacher] Joint already active"
      << std::endl;
    return;
  }

  std::cout << "[LinkAttacher] CreateJoint()" << std::endl;

  Entity parentLink = FindLink(_ecm, model1, link1);
  Entity childLink  = FindLink(_ecm, model2, link2);

  std::cout
    << "[LinkAttacher] parentLink="
    << parentLink
    << " childLink="
    << childLink
    << std::endl;

  if(parentLink == kNullEntity || childLink == kNullEntity)
  {
    std::cout << "[LinkAttacher] ERROR: link entities invalid" << std::endl;
    return;
  }

  Entity jointEntity = _ecm.CreateEntity();
  activeJoint = jointEntity;

  std::cout << "[LinkAttacher] Joint entity created: "
            << jointEntity << std::endl;

  components::DetachableJoint joint;

  joint.Data().parentLink = parentLink;
  joint.Data().childLink  = childLink;

  _ecm.CreateComponent(jointEntity, joint);
  
  std::cout
    << "[LinkAttacher] JOINT SUCCESSFULLY CREATED"
    << std::endl;

  std::cout << "[LinkAttacher] DetachableJoint component inserted" << std::endl;
}

void RemoveJoint(EntityComponentManager &_ecm)
{

  std::cout << "[LinkAttacher] RemoveJoint()" << std::endl;

  if(activeJoint == kNullEntity)
  {
    std::cout << "[LinkAttacher] No active joint" << std::endl;
    return;
  }

  _ecm.RequestRemoveEntity(activeJoint);

  std::cout << "[LinkAttacher] Joint entity removed" << std::endl;

  activeJoint = kNullEntity;

  contactLatched = false;
}


private:

rclcpp::Node::SharedPtr node;
rclcpp::executors::SingleThreadedExecutor::SharedPtr executor;

rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr gripperStateSub;

std::thread rosThread;

Entity worldEntity{kNullEntity};

bool initialized=false;
bool autoAttachEnabled = false;
bool removeJointRequested = false;
bool contactLatched = false;
bool createJointRequested = false;

std::string model1;
std::string link1;
std::string model2;
std::string link2;

Entity activeJoint{kNullEntity};

};

}

GZ_ADD_PLUGIN(
  gz_link_attacher::LinkAttacher,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)