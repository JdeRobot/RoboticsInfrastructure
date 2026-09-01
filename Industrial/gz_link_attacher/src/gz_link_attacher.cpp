#include <gz/sim/System.hh>

#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/DetachableJoint.hh>

#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/contacts.pb.h>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/bool.hpp>
#include <std_msgs/msg/string.hpp>

#include <thread>
#include <mutex>
#include <chrono>
#include <iostream>
#include <vector>
#include <sstream>
#include <string>
#include <algorithm>
#include <cctype>

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
  const std::shared_ptr<const sdf::Element> &_sdf,
  EntityComponentManager &,
  EventManager &) override
{

  std::cout << "\n[LinkAttacher] Configure() START\n";

  worldEntity = _entity;

  if (_sdf && _sdf->HasElement("robot_model"))
  {
      robotModelName = _sdf->Get<std::string>("robot_model");
  }

  if (robotModelName.empty())
  {
      std::cerr
          << "[LinkAttacher] ERROR: robot_model parameter not provided"
          << std::endl;

      return;
  }

  std::cout
      << "[LinkAttacher] Robot model: "
      << robotModelName
      << std::endl;

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
      std::lock_guard<std::mutex> lock(mutex);

      autoAttachEnabled = msg->data;

      std::cout
        << "[LinkAttacher] autoAttachEnabled="
        << autoAttachEnabled
        << std::endl;

      if (!autoAttachEnabled)
      {
        contactLatched = false;

        leftFingerContact = false;
        rightFingerContact = false;

        leftObjectModel.clear();
        rightObjectModel.clear();

        if (activeJoint != kNullEntity)
        {
            removeJointRequested = true;
        }
      }
    });

    graspableObjectsSub =
    node->create_subscription<std_msgs::msg::String>(
      "/graspable_objects",
      10,
      [this](const std_msgs::msg::String::SharedPtr msg)
      {
        std::lock_guard<std::mutex> lock(mutex);

        graspableObjects.clear();

        std::stringstream ss(msg->data);

        std::string item;

        while (std::getline(ss, item, ','))
        {
          item.erase(
            std::remove_if(item.begin(), item.end(), ::isspace),
            item.end()
          );

          graspableObjects.push_back(item);
        }
      });

  // Optional SDF params — defaults preserve pick_place (Robotiq) behaviour
  if (_sdf->HasElement("robot_model_name"))
    robotModelName = _sdf->Get<std::string>("robot_model_name");
  if (_sdf->HasElement("gripper_link_name"))
    gripperLinkName = _sdf->Get<std::string>("gripper_link_name");

  std::cout << "[LinkAttacher] robot_model_name=" << robotModelName << std::endl;
  std::cout << "[LinkAttacher] gripper_link_name=" << gripperLinkName << std::endl;

  std::cout << "[LinkAttacher] Subscribing to contact topics" << std::endl;

  if (!gripperLinkName.empty())
  {
    // Suction mode: single contact sensor on the configured gripper link
    std::string topic = "/world/default/model/" + robotModelName +
      "/link/" + gripperLinkName + "/sensor/suction_contact/contact";
    gzNode.Subscribe(topic, &LinkAttacher::OnContact, this);
  }
  else
  {
    // Robotiq finger-tip mode (pick_place default)
    std::string leftTopic =
        "/world/default/model/" + robotModelName +
        "/link/robotiq_85_left_finger_tip_link/sensor/left_finger_contact/contact";

    std::string rightTopic =
        "/world/default/model/" + robotModelName +
        "/link/robotiq_85_right_finger_tip_link/sensor/right_finger_contact/contact";

    gzNode.Subscribe(leftTopic,
                    &LinkAttacher::OnContact,
                    this);

    gzNode.Subscribe(rightTopic,
                    &LinkAttacher::OnContact,
                    this);
  }

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
  std::lock_guard<std::mutex> lock(mutex);

  if(!initialized)
  {
    std::cout << "[LinkAttacher] First PreUpdate() detected" << std::endl;
    initialized = true;
  } 

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

void OnContact(const gz::msgs::Contacts &_msg)
{
  std::lock_guard<std::mutex> lock(mutex);

  std::cout
    << "[LinkAttacher] contact_size="
    << _msg.contact_size()
    << std::endl;

  std::cout
    << "[LinkAttacher] autoAttachEnabled="
    << autoAttachEnabled
    << std::endl;

  if (!autoAttachEnabled)
    return;

  if (contactLatched)
    return;

  if (activeJoint != kNullEntity)
    return;

  if (createJointRequested)
    return;

  std::cout
    << "\n[LinkAttacher] CONTACT MESSAGE RECEIVED"
    << std::endl;

  for (int i = 0; i < _msg.contact_size(); ++i)
  {
    const auto &contact = _msg.contact(i);

    std::string collision1 =
      contact.collision1().name();

    std::string collision2 =
      contact.collision2().name();

    std::cout
      << "[LinkAttacher] collision1="
      << collision1
      << std::endl;

    std::cout
      << "[LinkAttacher] collision2="
      << collision2
      << std::endl;

    std::string objectModel;
    std::string hitCollision;

    for (const auto &obj : graspableObjects)
    {
      if (collision1.find(obj) != std::string::npos)
      {
        objectModel = obj;
        hitCollision = collision1;
        break;
      }
      else if (collision2.find(obj) != std::string::npos)
      {
        objectModel = obj;
        hitCollision = collision2;
        break;
      }
    }

    if (objectModel.empty())
    {
      continue;
    }

    std::cout
      << "[LinkAttacher] OBJECT DETECTED -> "
      << objectModel
      << std::endl;

<<<<<<< HEAD
    bool leftFinger =
        collision1.find("left_finger") != std::string::npos ||
        collision2.find("left_finger") != std::string::npos;

    if (leftFinger)
=======
    model1 = robotModelName;
    if (!gripperLinkName.empty())
    {
      // Suction mode: attach at the configured gripper link
      link1 = gripperLinkName;
    }
    else if (collision1.find("left_finger") != std::string::npos ||
             collision2.find("left_finger") != std::string::npos)
>>>>>>> origin/humble-devel
    {
      leftFingerContact = true;
        leftObjectModel = objectModel;

        std::cout << "[LinkAttacher] LEFT finger touched "
                  << objectModel << std::endl;
    }
    else
    {
      rightFingerContact = true;
        rightObjectModel = objectModel;

        std::cout << "[LinkAttacher] RIGHT finger touched "
                  << objectModel << std::endl;
    }
    if (leftFingerContact &&
        rightFingerContact &&
        leftObjectModel != rightObjectModel)
    {
        leftFingerContact = false;
        rightFingerContact = false;

<<<<<<< HEAD
        leftObjectModel.clear();
        rightObjectModel.clear();
=======
    // Extract actual model name from collision string (e.g. "box_89_0::link::collision")
    size_t pos = hitCollision.find("::");
    if (pos != std::string::npos) {
        model2 = hitCollision.substr(0, pos);
    } else {
        model2 = objectModel;
    }
>>>>>>> origin/humble-devel

        continue;
    }
    if (leftFingerContact &&
        rightFingerContact &&
        leftObjectModel == rightObjectModel)
    {
        model1 = robotModelName;

        link1 = "robotiq_85_left_finger_tip_link";

        model2 = leftObjectModel;
        link2 = "link";

        createJointRequested = true;
        contactLatched = true;

        leftFingerContact = false;
        rightFingerContact = false;

        leftObjectModel.clear();
        rightObjectModel.clear();

        std::cout
            << "[LinkAttacher] BOTH fingers touching -> creating joint"
            << std::endl; 

        break;
    }
  }
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


  leftFingerContact = false;
  rightFingerContact = false;

  leftObjectModel.clear();
  rightObjectModel.clear();
}


private:

rclcpp::Node::SharedPtr node;
rclcpp::executors::SingleThreadedExecutor::SharedPtr executor;

rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr gripperStateSub;
rclcpp::Subscription<std_msgs::msg::String>::SharedPtr graspableObjectsSub;

std::thread rosThread;

Entity worldEntity{kNullEntity};

bool initialized=false;
bool autoAttachEnabled = false;
bool removeJointRequested = false;
bool contactLatched = false;
bool createJointRequested = false;

bool leftFingerContact = false;
bool rightFingerContact = false;

std::string leftObjectModel;
std::string rightObjectModel;

gz::transport::Node gzNode;

<<<<<<< HEAD
std::string robotModelName;

=======
std::string robotModelName{"ur5_robotiq"};
std::string gripperLinkName{""};
>>>>>>> origin/humble-devel

std::string model1;
std::string link1;
std::string model2;
std::string link2;

std::mutex mutex;
std::vector<std::string> graspableObjects;

Entity activeJoint{kNullEntity};

};

}

GZ_ADD_PLUGIN(
  gz_link_attacher::LinkAttacher,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)