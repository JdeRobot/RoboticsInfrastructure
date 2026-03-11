#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Entity.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/components/Joint.hh>
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
  public ISystemConfigure
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
      rclcpp::init(0,nullptr);

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

private:

  rclcpp::Node::SharedPtr node;

  rclcpp::Service<linkattacher_msgs::srv::AttachLink>::SharedPtr attachService;
  rclcpp::Service<linkattacher_msgs::srv::DetachLink>::SharedPtr detachService;

  Entity worldEntity;

  bool attached=false;

  std::string jointName;

  /////////////////////////////////////////////////////////////

  Entity FindLink(
      EntityComponentManager &_ecm,
      const std::string &modelName,
      const std::string &linkName)
  {

    Entity result{kNullEntity};

    _ecm.Each<components::Name,components::ParentEntity>(
      [&](const Entity &_entity,
          const components::Name *_name,
          const components::ParentEntity *_parent)
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

  /////////////////////////////////////////////////////////////

  void Attach(
    const std::shared_ptr<linkattacher_msgs::srv::AttachLink::Request> req,
    std::shared_ptr<linkattacher_msgs::srv::AttachLink::Response> res)
  {

    if(attached)
    {
      res->success=false;
      res->message="Already attached";
      return;
    }

    // Aquí normalmente crearíamos el joint
    // pero para primera versión solo confirmamos

    jointName =
      req->model1_name + "_" +
      req->link1_name + "_" +
      req->model2_name + "_" +
      req->link2_name + "_joint";

    attached=true;

    res->success=true;
    res->message="Attached";

  }

  /////////////////////////////////////////////////////////////

  void Detach(
    const std::shared_ptr<linkattacher_msgs::srv::DetachLink::Request> req,
    std::shared_ptr<linkattacher_msgs::srv::DetachLink::Response> res)
  {

    if(!attached)
    {
      res->success=false;
      res->message="Nothing attached";
      return;
    }

    attached=false;

    res->success=true;
    res->message="Detached";

  }

};

}

GZ_ADD_PLUGIN(
  gz_link_attacher::LinkAttacher,
  gz::sim::System,
  gz::sim::ISystemConfigure
)