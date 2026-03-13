#include <gz/sim/System.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Model.hh>

#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/Joint.hh>
#include <gz/sim/components/JointType.hh>
#include <gz/sim/components/JointChild.hh>

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

    executor.add_node(node);

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

    RCLCPP_INFO(node->get_logger(),"LinkAttacher plugin ready");
  }

  void PreUpdate(
    const UpdateInfo &,
    EntityComponentManager &_ecm) override
  {

    executor.spin_some();

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
  rclcpp::executors::SingleThreadedExecutor executor;

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

/*  FIND MODEL ENTITY  */

  Entity FindModel(
      EntityComponentManager &_ecm,
      const std::string &modelName)
  {

    Entity modelEntity{kNullEntity};

    _ecm.Each<components::Name>(
      [&](const Entity &_entity,
          const components::Name *_name)
      {

        if (_name->Data() == modelName)
        {
          modelEntity = _entity;
          return false;
        }

        return true;
      });

    return modelEntity;
  }

/*  FIND LINK INSIDE MODEL  */

  Entity FindLink(
      EntityComponentManager &_ecm,
      const Entity &modelEntity,
      const std::string &linkName)
  {

    Entity result{kNullEntity};

    _ecm.Each<components::Name, components::ParentEntity>(
      [&](const Entity &_entity,
          const components::Name *_name,
          const components::ParentEntity *_parent)
      {

        if (_name->Data() == linkName &&
            _parent->Data() == modelEntity)
        {
          result = _entity;
          return false;
        }

        return true;
      });

    return result;
  }

/*  CREATE JOINT  */

  void CreateJoint(EntityComponentManager &_ecm)
  {

    Entity model1Entity = FindModel(_ecm, model1);
    Entity model2Entity = FindModel(_ecm, model2);

    if (model1Entity == kNullEntity || model2Entity == kNullEntity)
    {
      RCLCPP_ERROR(node->get_logger(),"Model not found");
      return;
    }

    Entity parentLink = FindLink(_ecm, model1Entity, link1);
    Entity childLink  = FindLink(_ecm, model2Entity, link2);

    if (parentLink == kNullEntity || childLink == kNullEntity)
    {
      RCLCPP_ERROR(node->get_logger(),"Link not found");
      return;
    }

    jointEntity = _ecm.CreateEntity();

    _ecm.CreateComponent(jointEntity, components::Joint());

    _ecm.CreateComponent(
      jointEntity,
      components::Name("dynamic_attach_joint"));

    _ecm.CreateComponent(
      jointEntity,
      components::ParentEntity(parentLink));

    _ecm.CreateComponent(
      jointEntity,
      components::JointChild(childLink));

    _ecm.CreateComponent(
      jointEntity,
      components::JointType(sdf::JointType::FIXED));

    RCLCPP_INFO(
      node->get_logger(),
      "Joint CREATED: %s::%s -> %s::%s",
      model1.c_str(),
      link1.c_str(),
      model2.c_str(),
      link2.c_str());

  }

/*  REMOVE JOINT  */

  void RemoveJoint(EntityComponentManager &_ecm)
  {

    if (jointEntity == kNullEntity)
      return;

    _ecm.RequestRemoveEntity(jointEntity);

    jointEntity = kNullEntity;

    RCLCPP_INFO(node->get_logger(),"Joint REMOVED");

  }

/*  SERVICE CALLBACKS  */

  void Attach(
    const std::shared_ptr<linkattacher_msgs::srv::AttachLink::Request> req,
    std::shared_ptr<linkattacher_msgs::srv::AttachLink::Response> res)
  {

    model1 = req->model1_name;
    link1  = req->link1_name;
    model2 = req->model2_name;
    link2  = req->link2_name;

    attachRequested = true;

    RCLCPP_INFO(
      node->get_logger(),
      "Attach request received");

    res->success = true;
    res->message = "Attach scheduled";

  }

  void Detach(
    const std::shared_ptr<linkattacher_msgs::srv::DetachLink::Request>,
    std::shared_ptr<linkattacher_msgs::srv::DetachLink::Response> res)
  {

    detachRequested = true;

    RCLCPP_INFO(
      node->get_logger(),
      "Detach request received");

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