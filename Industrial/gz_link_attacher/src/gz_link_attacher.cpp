#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>

#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/DetachableJoint.hh>

#include <gz/plugin/Register.hh>

#include <rclcpp/rclcpp.hpp>

#include <linkattacher_msgs/srv/attach_link.hpp>
#include <linkattacher_msgs/srv/detach_link.hpp>

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

  void Configure(
      const Entity &_entity,
      const std::shared_ptr<const sdf::Element> &,
      EntityComponentManager &_ecm,
      EventManager &) override
  {

    std::cout << "[LinkAttacher] Configure() called" << std::endl;

    worldEntity = _entity;

    if (!rclcpp::ok())
    {
      std::cout << "[LinkAttacher] Initializing ROS2" << std::endl;
      rclcpp::init(0, nullptr);
    }

    node = std::make_shared<rclcpp::Node>("gz_link_attacher");

    std::cout << "[LinkAttacher] Creating ROS services" << std::endl;

    attachService =
      node->create_service<linkattacher_msgs::srv::AttachLink>(
        "ATTACHLINK",
        std::bind(
          &LinkAttacher::Attach,
          this,
          std::placeholders::_1,
          std::placeholders::_2));

    detachService =
      node->create_service<linkattacher_msgs::srv::DetachLink>(
        "DETACHLINK",
        std::bind(
          &LinkAttacher::Detach,
          this,
          std::placeholders::_1,
          std::placeholders::_2));

    std::cout << "[LinkAttacher] Plugin READY" << std::endl;
  }


  void PreUpdate(
    const UpdateInfo &,
    EntityComponentManager &_ecm) override
  {

    if (node)
      rclcpp::spin_some(node);

    if (attachRequested)
    {
      std::cout << "[LinkAttacher] attachRequested detected in PreUpdate" << std::endl;

      CreateJoint(_ecm);

      attachRequested=false;
    }

    if (detachRequested)
    {
      std::cout << "[LinkAttacher] detachRequested detected in PreUpdate" << std::endl;

      RemoveJoint(_ecm);

      detachRequested=false;
    }

  }

private:

  rclcpp::Node::SharedPtr node;

  rclcpp::Service<linkattacher_msgs::srv::AttachLink>::SharedPtr attachService;
  rclcpp::Service<linkattacher_msgs::srv::DetachLink>::SharedPtr detachService;

  Entity worldEntity{kNullEntity};

  bool attachRequested=false;
  bool detachRequested=false;

  std::string model1;
  std::string link1;
  std::string model2;
  std::string link2;


  Entity FindLink(
      EntityComponentManager &_ecm,
      const std::string &linkName)
  {

    std::cout << "[LinkAttacher] Searching link: " << linkName << std::endl;

    Entity result{kNullEntity};

    _ecm.Each<components::Name>(
      [&](const Entity &_entity,
          const components::Name *_name)
      {

        std::string currentName = _name->Data();

        if (currentName == linkName)
        {
          std::cout << "[LinkAttacher] FOUND LINK: " << currentName << std::endl;

          result=_entity;
          return false;
        }

        return true;

      });

    if (result == kNullEntity)
    {
      std::cout << "[LinkAttacher] LINK NOT FOUND: " << linkName << std::endl;
    }

    return result;
  }


  void CreateJoint(EntityComponentManager &_ecm)
  {

    std::cout << "[LinkAttacher] CreateJoint() called" << std::endl;

    std::cout << "[LinkAttacher] Parent model: " << model1 << std::endl;
    std::cout << "[LinkAttacher] Parent link: " << link1 << std::endl;

    std::cout << "[LinkAttacher] Child model: " << model2 << std::endl;
    std::cout << "[LinkAttacher] Child link: " << link2 << std::endl;

    Entity parentLink = FindLink(_ecm, link1);
    Entity childLink = FindLink(_ecm, link2);

    if (parentLink == kNullEntity || childLink == kNullEntity)
    {
      std::cout << "[LinkAttacher] ERROR: Links not found" << std::endl;
      return;
    }

    std::cout << "[LinkAttacher] Creating DetachableJoint component" << std::endl;

    components::DetachableJoint joint;

    joint.Data().parentLink = parentLink;
    joint.Data().childLink = childLink;

    _ecm.CreateComponent(parentLink, joint);

    std::cout << "[LinkAttacher] SUCCESS: Joint created" << std::endl;
  }


  void RemoveJoint(EntityComponentManager &_ecm)
  {

    std::cout << "[LinkAttacher] RemoveJoint() called" << std::endl;

    Entity parentLink = FindLink(_ecm, link1);

    if (parentLink == kNullEntity)
    {
      std::cout << "[LinkAttacher] Parent link not found for detach" << std::endl;
      return;
    }

    auto joint =
      _ecm.Component<components::DetachableJoint>(parentLink);

    if (joint)
    {
      std::cout << "[LinkAttacher] Removing DetachableJoint component" << std::endl;

      _ecm.RemoveComponent<components::DetachableJoint>(parentLink);

      std::cout << "[LinkAttacher] SUCCESS: Joint removed" << std::endl;
    }
    else
    {
      std::cout << "[LinkAttacher] No DetachableJoint found on parent link" << std::endl;
    }

  }


  void Attach(
    const std::shared_ptr<linkattacher_msgs::srv::AttachLink::Request> req,
    std::shared_ptr<linkattacher_msgs::srv::AttachLink::Response> res)
  {

    std::cout << "[LinkAttacher] ATTACH SERVICE CALLED" << std::endl;

    model1 = req->model1_name;
    link1 = req->link1_name;
    model2 = req->model2_name;
    link2 = req->link2_name;

    std::cout << "[LinkAttacher] model1: " << model1 << std::endl;
    std::cout << "[LinkAttacher] link1: " << link1 << std::endl;
    std::cout << "[LinkAttacher] model2: " << model2 << std::endl;
    std::cout << "[LinkAttacher] link2: " << link2 << std::endl;

    attachRequested = true;

    res->success = true;
    res->message = "Attach scheduled";

    std::cout << "[LinkAttacher] attachRequested set TRUE" << std::endl;

  }


  void Detach(
    const std::shared_ptr<linkattacher_msgs::srv::DetachLink::Request>,
    std::shared_ptr<linkattacher_msgs::srv::DetachLink::Response> res)
  {

    std::cout << "[LinkAttacher] DETACH SERVICE CALLED" << std::endl;

    detachRequested = true;

    res->success = true;
    res->message = "Detach scheduled";

    std::cout << "[LinkAttacher] detachRequested set TRUE" << std::endl;

  }

};

}

GZ_ADD_PLUGIN(
  gz_link_attacher::LinkAttacher,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)