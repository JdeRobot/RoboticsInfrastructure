#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Util.hh>

#include <gz/sim/components/Joint.hh>
#include <gz/sim/components/JointType.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>

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

///////////////////////////////////////////////////////////////

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

///////////////////////////////////////////////////////////////

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

///////////////////////////////////////////////////////////////

private:

  rclcpp::Node::SharedPtr node;

  rclcpp::Service<linkattacher_msgs::srv::AttachLink>::SharedPtr attachService;
  rclcpp::Service<linkattacher_msgs::srv::DetachLink>::SharedPtr detachService;

  Entity worldEntity{kNullEntity};
  Entity jointEntity{kNullEntity};

  bool attachRequested=false;
  bool detachRequested=false;

  std::string model1;
  std::string link1;
  std::string model2;
  std::string link2;

///////////////////////////////////////////////////////////////

  Entity FindLink(
      EntityComponentManager &_ecm,
      const std::string &modelName,
      const std::string &linkName)
  {

    Entity linkEntity{kNullEntity};

    _ecm.Each<components::Name, components::ParentEntity>(
      [&](const Entity &_entity,
          const components::Name *_name,
          const components::ParentEntity *_parent)
      {

        if (_name->Data()==linkName)
        {
          linkEntity=_entity;
          return false;
        }

        return true;

      });

    return linkEntity;
  }

///////////////////////////////////////////////////////////////

  void CreateJoint(EntityComponentManager &_ecm)
  {

    Entity link1Entity = FindLink(_ecm, model1, link1);
    Entity link2Entity = FindLink(_ecm, model2, link2);

    if (link1Entity == kNullEntity || link2Entity == kNullEntity)
    {
      RCLCPP_ERROR(node->get_logger(),"Links not found");
      return;
    }

    jointEntity = _ecm.CreateEntity();

    _ecm.CreateComponent(
      jointEntity,
      components::Joint());

    _ecm.CreateComponent(
      jointEntity,
      components::Name("dynamic_attach_joint"));

    _ecm.CreateComponent(
      jointEntity,
      components::ParentEntity(link1Entity));

    _ecm.CreateComponent(
      jointEntity,
      components::JointType(sdf::JointType::FIXED));

    RCLCPP_INFO(node->get_logger(),"Joint created");

  }

///////////////////////////////////////////////////////////////

  void RemoveJoint(EntityComponentManager &_ecm)
  {

    if (jointEntity == kNullEntity)
      return;

    _ecm.RequestRemoveEntity(jointEntity);

    jointEntity = kNullEntity;

    RCLCPP_INFO(node->get_logger(),"Joint removed");

  }

///////////////////////////////////////////////////////////////

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

///////////////////////////////////////////////////////////////

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