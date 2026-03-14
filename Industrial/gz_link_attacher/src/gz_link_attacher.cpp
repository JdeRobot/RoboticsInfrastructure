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

#include <thread>
#include <chrono>
#include <iostream>
#include <mutex>

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

  std::cout << "[LinkAttacher] Creating ATTACH service" << std::endl;

  attachService =
    node->create_service<linkattacher_msgs::srv::AttachLink>(
      "/ATTACHLINK",
      std::bind(
        &LinkAttacher::Attach,
        this,
        std::placeholders::_1,
        std::placeholders::_2,
        std::placeholders::_3));

  std::cout << "[LinkAttacher] ATTACH service created" << std::endl;

  std::cout << "[LinkAttacher] Creating DETACH service" << std::endl;

  detachService =
    node->create_service<linkattacher_msgs::srv::DetachLink>(
      "/DETACHLINK",
      std::bind(
        &LinkAttacher::Detach,
        this,
        std::placeholders::_1,
        std::placeholders::_2,
        std::placeholders::_3));

  std::cout << "[LinkAttacher] DETACH service created" << std::endl;

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

  if(attachRequested)
  {
    std::cout << "\n[LinkAttacher] Processing attach request" << std::endl;
    std::cout << "[LinkAttacher] model1=" << model1
              << " link1=" << link1 << std::endl;
    std::cout << "[LinkAttacher] model2=" << model2
              << " link2=" << link2 << std::endl;

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

  std::cout << "[LinkAttacher] CreateJoint()" << std::endl;

  Entity parentLink = FindLink(_ecm, model1, link1);
  Entity childLink  = FindLink(_ecm, model2, link2);

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

  _ecm.RemoveComponent<components::DetachableJoint>(activeJoint);
  _ecm.RequestRemoveEntity(activeJoint);

  std::cout << "[LinkAttacher] Active joint removed" << std::endl;

  activeJoint = kNullEntity;
}

void Attach(
  const std::shared_ptr<rmw_request_id_t>,
  const std::shared_ptr<linkattacher_msgs::srv::AttachLink::Request> req,
  std::shared_ptr<linkattacher_msgs::srv::AttachLink::Response> res)
{

  std::cout<<"\n==============================="<<std::endl;
  std::cout<<"[LinkAttacher] ATTACH REQUEST RECEIVED"<<std::endl;

  std::cout<<"model1="<<req->model1_name<<std::endl;
  std::cout<<"link1="<<req->link1_name<<std::endl;
  std::cout<<"model2="<<req->model2_name<<std::endl;
  std::cout<<"link2="<<req->link2_name<<std::endl;

  model1=req->model1_name;
  link1=req->link1_name;

  model2=req->model2_name;
  link2=req->link2_name;

  attachRequested=true;

  res->success=true;
  res->message="Attach scheduled";

  std::cout<<"[LinkAttacher] Response sent"<<std::endl;
  std::cout<<"===============================\n"<<std::endl;
}

void Detach(
  const std::shared_ptr<rmw_request_id_t>,
  const std::shared_ptr<linkattacher_msgs::srv::DetachLink::Request>,
  std::shared_ptr<linkattacher_msgs::srv::DetachLink::Response> res)
{

  std::cout<<"\n[LinkAttacher] DETACH REQUEST RECEIVED"<<std::endl;

  detachRequested=true;

  res->success=true;
  res->message="Detach scheduled";

  std::cout<<"[LinkAttacher] Detach response sent"<<std::endl;
}

private:

rclcpp::Node::SharedPtr node;
rclcpp::executors::SingleThreadedExecutor::SharedPtr executor;

rclcpp::Service<linkattacher_msgs::srv::AttachLink>::SharedPtr attachService;
rclcpp::Service<linkattacher_msgs::srv::DetachLink>::SharedPtr detachService;

std::thread rosThread;

Entity worldEntity{kNullEntity};

bool attachRequested=false;
bool detachRequested=false;
bool initialized=false;

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