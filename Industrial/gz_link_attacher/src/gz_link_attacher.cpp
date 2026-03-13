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

    worldEntity = _entity;

    if (!rclcpp::ok())
      rclcpp::init(0, nullptr);

    node = std::make_shared<rclcpp::Node>("gz_link_attacher");

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

    RCLCPP_INFO(node->get_logger(),"GZ Link Attacher Loaded");
  }


  void PreUpdate(
    const UpdateInfo &,
    EntityComponentManager &_ecm) override
  {

    if (node)
      rclcpp::spin_some(node);

    if (attachRequested)
    {
      CreateJoint(_ecm);
      attachRequested=false;
    }

    if (detachRequested)
    {
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

    Entity result{kNullEntity};

    _ecm.Each<components::Name>(
      [&](const Entity &_entity,
          const components::Name *_name)
      {

        if (_name->Data()==linkName)
        {
          result=_entity;
          return false;
        }

        return true;

      });

    return result;
  }


  void CreateJoint(EntityComponentManager &_ecm)
  {

    Entity parentLink = FindLink(_ecm, link1);
    Entity childLink = FindLink(_ecm, link2);

    if (parentLink == kNullEntity || childLink == kNullEntity)
    {
      RCLCPP_ERROR(node->get_logger(),"Links not found");
      return;
    }

    _ecm.CreateComponent(
      parentLink,
      components::DetachableJoint({childLink})
    );

    RCLCPP_INFO(node->get_logger(),
      "Attached %s to %s",
      link2.c_str(),
      link1.c_str());
  }


  void RemoveJoint(EntityComponentManager &_ecm)
  {

    Entity parentLink = FindLink(_ecm, link1);

    if (parentLink == kNullEntity)
      return;

    auto joint =
      _ecm.Component<components::DetachableJoint>(parentLink);

    if (joint)
    {
      _ecm.RemoveComponent<components::DetachableJoint>(parentLink);
      RCLCPP_INFO(node->get_logger(),"Detached");
    }

  }


  void Attach(
    const std::shared_ptr<linkattacher_msgs::srv::AttachLink::Request> req,
    std::shared_ptr<linkattacher_msgs::srv::AttachLink::Response> res)
  {

    model1 = req->model1_name;
    link1 = req->link1_name;
    model2 = req->model2_name;
    link2 = req->link2_name;

    attachRequested = true;

    res->success = true;
    res->message = "Attach scheduled";

  }


  void Detach(
    const std::shared_ptr<linkattacher_msgs::srv::DetachLink::Request>,
    std::shared_ptr<linkattacher_msgs::srv::DetachLink::Response> res)
  {

    detachRequested = true;

    res->success = true;
    res->message = "Detach scheduled";

  }

};

}

GZ_ADD_PLUGIN(
  gz_link_attacher::LinkAttacher,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)