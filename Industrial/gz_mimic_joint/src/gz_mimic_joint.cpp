#include <gz/sim/System.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/JointPosition.hh>

#include <gz/plugin/Register.hh>

#include <iostream>

using namespace gz;
using namespace sim;

namespace gz_mimic_joint
{

class MimicJoint :
  public System,
  public ISystemConfigure,
  public ISystemPreUpdate
{

public:

void Configure(
  const Entity &_entity,
  const std::shared_ptr<const sdf::Element> &_sdf,
  EntityComponentManager &_ecm,
  EventManager &) override
{
  std::cout << "\n[MimicJoint] Configure() START\n";

  worldEntity = _entity;

  if (_sdf->HasElement("parent_joint"))
    parent_joint_name = _sdf->Get<std::string>("parent_joint");

  if (_sdf->HasElement("mimic_joint"))
    mimic_joint_name = _sdf->Get<std::string>("mimic_joint");

  std::cout << "[MimicJoint] parent_joint: " << parent_joint_name << std::endl;
  std::cout << "[MimicJoint] mimic_joint : " << mimic_joint_name << std::endl;

  std::cout << "[MimicJoint] Configure() END\n\n";
}

void PreUpdate(
  const UpdateInfo &,
  EntityComponentManager &_ecm) override
{
  // Buscar joints solo una vez
  if (parentJoint == kNullEntity)
  {
    parentJoint = FindJoint(_ecm, parent_joint_name);

    if (parentJoint != kNullEntity)
      std::cout << "[MimicJoint] Parent joint found\n";
  }

  if (mimicJoint == kNullEntity)
  {
    mimicJoint = FindJoint(_ecm, mimic_joint_name);

    if (mimicJoint != kNullEntity)
      std::cout << "[MimicJoint] Mimic joint found\n";
  }

  if (parentJoint != kNullEntity && mimicJoint != kNullEntity)
  {
    auto parentPos = _ecm.Component<components::JointPosition>(parentJoint);

    if (parentPos && !parentPos->Data().empty())
    {
      _ecm.SetComponentData(
        mimicJoint,
        components::JointPosition({parentPos->Data()[0]})
      );
    }
  }
}

private:

Entity FindJoint(EntityComponentManager &_ecm, const std::string &jointName)
{
  Entity result{kNullEntity};

  _ecm.Each<components::Name>(
    [&](const Entity &_entity, const components::Name *_name)
    {
      if (_name->Data() == jointName)
      {
        result = _entity;
        return false;
      }
      return true;
    });

  if (result == kNullEntity)
  {
    std::cout << "[MimicJoint] Joint NOT found: " << jointName << std::endl;
  }

  return result;
}

private:

Entity worldEntity{kNullEntity};

std::string parent_joint_name;
std::string mimic_joint_name;

Entity parentJoint{kNullEntity};
Entity mimicJoint{kNullEntity};

};

} 

GZ_ADD_PLUGIN(
  gz_mimic_joint::MimicJoint,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate
)