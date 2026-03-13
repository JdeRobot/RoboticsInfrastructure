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

/////////////////////////////////////////////////
void Configure(
  const Entity &_entity,
  const std::shared_ptr<const sdf::Element> &,
  EntityComponentManager &,
  EventManager &) override
{

  std::cout << "[LinkAttacher] Configure()" << std::endl;

  worldEntity = _entity;

  if (!rclcpp::ok())
  {
    rclcpp::init(0,nullptr);
  }

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

  std::cout << "[LinkAttacher] READY" << std::endl;
}

/////////////////////////////////////////////////
void PreUpdate(
  const UpdateInfo &,
  EntityComponentManager &_ecm) override
{

  if(node)
    rclcpp::spin_some(node);

  if(attachRequested)
  {
    std::cout << "[LinkAttacher] Processing attach request" << std::endl;

    CreateJoint(_ecm);

    attachRequested=false;
  }

  if(detachRequested)
  {
    std::cout << "[LinkAttacher] Processing detach request" << std::endl;

    RemoveJoint(_ecm);

    detachRequested=false;
  }

}

private:

/////////////////////////////////////////////////
Entity FindLink(
  EntityComponentManager &_ecm,
  const std::string &modelName,
  const std::string &linkName)
{

  Entity modelEntity{kNullEntity};

  _ecm.Each<components::Name>(
    [&](const Entity &_entity,const components::Name *_name)
    {

      if(_name->Data()==modelName)
      {
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

  Entity result{kNullEntity};

  _ecm.Each<components::Name,components::ParentEntity>(
    [&](const Entity &_entity,
        const components::Name *_name,
        const components::ParentEntity *_parent)
    {

      if(_name->Data()==linkName && _parent->Data()==modelEntity)
      {
        result=_entity;
        return false;
      }

      return true;

    });

  if(result==kNullEntity)
  {
    std::cout<<"[LinkAttacher] LINK NOT FOUND: "<<modelName<<"::"<<linkName<<std::endl;
  }

  return result;
}

/////////////////////////////////////////////////
void CreateJoint(EntityComponentManager &_ecm)
{

  std::cout<<"[LinkAttacher] Creating joint"<<std::endl;

  Entity parentLink = FindLink(_ecm,model1,link1);
  Entity childLink  = FindLink(_ecm,model2,link2);

  if(parentLink==kNullEntity || childLink==kNullEntity)
  {
    std::cout<<"[LinkAttacher] ERROR links not found"<<std::endl;
    return;
  }

  components::DetachableJoint joint;

  joint.Data().parentLink = parentLink;
  joint.Data().childLink  = childLink;

  _ecm.CreateComponent(parentLink,joint);

  std::cout<<"[LinkAttacher] Joint created successfully"<<std::endl;
}

/////////////////////////////////////////////////
void RemoveJoint(EntityComponentManager &_ecm)
{

  Entity parentLink = FindLink(_ecm,model1,link1);

  if(parentLink==kNullEntity)
  {
    std::cout<<"[LinkAttacher] Parent link not found"<<std::endl;
    return;
  }

  auto joint =
    _ecm.Component<components::DetachableJoint>(parentLink);

  if(joint)
  {
    _ecm.RemoveComponent<components::DetachableJoint>(parentLink);

    std::cout<<"[LinkAttacher] Joint removed"<<std::endl;
  }
  else
  {
    std::cout<<"[LinkAttacher] No joint to remove"<<std::endl;
  }

}

/////////////////////////////////////////////////
void Attach(
  const std::shared_ptr<linkattacher_msgs::srv::AttachLink::Request> req,
  std::shared_ptr<linkattacher_msgs::srv::AttachLink::Response> res)
{

  std::cout<<"[LinkAttacher] ATTACH REQUEST"<<std::endl;

  model1=req->model1_name;
  link1=req->link1_name;

  model2=req->model2_name;
  link2=req->link2_name;

  attachRequested=true;

  res->success=true;
  res->message="Attach scheduled";

}

/////////////////////////////////////////////////
void Detach(
  const std::shared_ptr<linkattacher_msgs::srv::DetachLink::Request>,
  std::shared_ptr<linkattacher_msgs::srv::DetachLink::Response> res)
{

  std::cout<<"[LinkAttacher] DETACH REQUEST"<<std::endl;

  detachRequested=true;

  res->success=true;
  res->message="Detach scheduled";

}

/////////////////////////////////////////////////

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

};

}

GZ_ADD_PLUGIN(
  gz_link_attacher::LinkAttacher,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)