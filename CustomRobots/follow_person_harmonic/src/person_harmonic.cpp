#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/plugin/Register.hh>

#include <gz/math/Pose3.hh>
#include <gz/math/Quaternion.hh>

#include <mutex>
#include <iostream>

namespace person_plugin
{
  class Person:
    public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate
  {
    private:
      gz::sim::Model model{gz::sim::kNullEntity};
      gz::math::Pose3d currentPose{0, 0, 0, 0, 0, 0};
      bool poseInitialized{false};

      double linear_speed{0.01};  // velocidad constante
      std::mutex mtx;

    public:
      Person() = default;

      void Configure(const gz::sim::Entity &_entity,
                     const std::shared_ptr<const sdf::Element> & /*_sdf*/,
                     gz::sim::EntityComponentManager &_ecm,
                     gz::sim::EventManager & /*_eventMgr*/) override
      {
        this->model = gz::sim::Model(_entity);

        if (!this->model.Valid(_ecm))
        {
          std::cerr << "[Person] Plugin must be attached to a model.\n";
          return;
        }

        this->currentPose = gz::sim::worldPose(this->model.Entity(), _ecm);
        this->poseInitialized = true;
      }

      void PreUpdate(const gz::sim::UpdateInfo &_info,
                     gz::sim::EntityComponentManager &_ecm) override
      {
        if (_info.paused || !this->poseInitialized || !this->model.Valid(_ecm))
          return;

        gz::math::Pose3d pose;
        {
          std::lock_guard<std::mutex> lock(this->mtx);
          pose = this->currentPose;
        }

        // orientación actual
        double yaw = pose.Rot().Yaw();

        // movimiento hacia delante
        pose.Pos().X() += this->linear_speed * std::cos(yaw);
        pose.Pos().Y() += this->linear_speed * std::sin(yaw);

        // aplicar en Harmonic
        this->model.SetWorldPoseCmd(_ecm, pose);

        // guardar
        {
          std::lock_guard<std::mutex> lock(this->mtx);
          this->currentPose = pose;
        }
      }
  };
}

GZ_ADD_PLUGIN(
  person_plugin::Person,
  gz::sim::System,
  person_plugin::Person::ISystemConfigure,
  person_plugin::Person::ISystemPreUpdate
)

GZ_ADD_PLUGIN_ALIAS(person_plugin::Person, "person_plugin::Person")