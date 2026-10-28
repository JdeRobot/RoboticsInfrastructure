#include <gz/sim/System.hh>

#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Model.hh>

#include <gz/plugin/Register.hh>

#include <gz/transport/Node.hh>
#include <gz/msgs/double.pb.h>

#include <iostream>
#include <memory>
#include <string>

namespace box_mover
{

class BoxMoverPlugin :
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  static constexpr double BELT_SPEED = -0.15;
  static constexpr double STOP_TIME = 10.0;
  bool started = false;
  bool beltStarted = false;
  bool stopped = false;
  double startTime = 0.0;
  gz::transport::Node transportNode;
  gz::transport::Node::Publisher speedPublisher;

  void Configure(
    const gz::sim::Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &_ecm,
    gz::sim::EventManager &_eventMgr) override
  {
    (void)_entity;
    (void)_sdf;
    (void)_ecm;
    (void)_eventMgr;

    speedPublisher =
      transportNode.Advertise<gz::msgs::Double>(
        "/model/conveyor_belt_1/link/link/track_cmd_vel");


    if (!speedPublisher)
    {
      std::cerr
        << "[BoxMoverPlugin] ERROR: no se pudo crear "
        << "el publisher del TrackController."
        << std::endl;
    }
    else
    {
      std::cout
        << "[BoxMoverPlugin] Publisher del TrackController creado."
        << std::endl;

      std::cout
        << "[BoxMoverPlugin] Topic: "
        << "/model/conveyor_belt_1/link/link/track_cmd_vel"
        << std::endl;
    }
  }

  void PreUpdate(
    const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager &_ecm) override
  {
    const double simTime = _info.simTime.count();

    if (stopped)
      return;

    bool sausageFound = false;


    _ecm.Each<
      gz::sim::components::Model,
      gz::sim::components::Name>(
      [&](const gz::sim::Entity &,
          const gz::sim::components::Model *,
          const gz::sim::components::Name *_name) -> bool
      {
        const std::string name = _name->Data();
        if (name.find("box_") != std::string::npos)
        {
          sausageFound = true;
          return false;
        }
        return true;
      });

    if (sausageFound && !started)
    {
      started = true;
      startTime = simTime;
      std::cout
        << "[BoxMoverPlugin] Primera salchicha detectada."
        << std::endl;
      std::cout
        << "[BoxMoverPlugin] Tiempo inicial = "
        << startTime
        << " s"
        << std::endl;
      std::cout
        << "[BoxMoverPlugin] Esperando conexion "
        << "con TrackController..."
        << std::endl;
    }

    if (started && !beltStarted)
    {
      if (speedPublisher.HasConnections())
      {
        beltStarted = true;
        std::cout
          << "[BoxMoverPlugin] TrackController conectado."
          << std::endl;
        std::cout
          << "[BoxMoverPlugin] Iniciando cinta a "
          << BELT_SPEED
          << " m/s."
          << std::endl;
        SetBeltSpeed(BELT_SPEED);
      }
    }

    if (started && beltStarted && !stopped)
    {
      const double elapsedTime =
        simTime - startTime;
    } 
    else
    {
      stopped = true;
      std::cout
        << "[BoxMoverPlugin] Han pasado "
        << STOP_TIME
        << " segundos."
        << std::endl;
      std::cout
        << "[BoxMoverPlugin] Deteniendo cinta."
        << std::endl;
      SetBeltSpeed(0.0);
    }
  }
  void SetBeltSpeed(double speed)
  {
    std::cout
      << "[BoxMoverPlugin] SetBeltSpeed("
      << speed
      << ")"
      << std::endl;
    const bool connected =
      speedPublisher.HasConnections();
    std::cout
      << "[BoxMoverPlugin] HasConnections = "
      << connected
      << std::endl;
    if (!speedPublisher)
    {
      std::cerr
        << "[BoxMoverPlugin] ERROR: publisher no disponible."
        << std::endl;
      return;
    }

    gz::msgs::Double msg;
    msg.set_data(speed);
    speedPublisher.Publish(msg);

    std::cout
      << "[BoxMoverPlugin] TrackController speed -> "
      << speed
      << " m/s"
      << std::endl;
  }
};

}

GZ_ADD_PLUGIN(
  box_mover::BoxMoverPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate)


GZ_ADD_PLUGIN_ALIAS(
  box_mover::BoxMoverPlugin,
  "box_mover::BoxMoverPlugin")