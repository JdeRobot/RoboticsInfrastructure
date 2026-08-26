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

  // ============================================================
  // CONFIGURACIÓN
  // ============================================================

  // Velocidad de la cinta.
  // Negativa = dirección -Y.
  static constexpr double BELT_SPEED = -0.15;

  // Tiempo que la cinta permanece funcionando
  // desde que aparece la primera salchicha.
  static constexpr double STOP_TIME = 10.0;


  // ============================================================
  // ESTADO
  // ============================================================

  bool started = false;

  bool stopped = false;

  double startTime = 0.0;


  // ============================================================
  // GAZEBO TRANSPORT
  // ============================================================

  gz::transport::Node transportNode;

  gz::transport::Node::Publisher speedPublisher;


  // ============================================================
  // CONFIGURE
  // ============================================================

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
        << "[BoxMoverPlugin] Publisher creado correctamente."
        << std::endl;
    }
  }


  // ============================================================
  // PREUPDATE
  // ============================================================

  void PreUpdate(
    const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager &_ecm) override
  {
    const double simTime = _info.simTime.count();


    // ==========================================================
    // SI YA ESTÁ PARADA
    // ==========================================================

    if (stopped)
      return;


    // ==========================================================
    // BUSCAR SALCHICHAS
    // ==========================================================

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

          // Ya hemos encontrado una salchicha.
          return false;
        }

        return true;
      });


    // ==========================================================
    // PRIMERA SALCHICHA
    // ==========================================================

    if (sausageFound && !started)
    {
      started = true;

      startTime = simTime;

      std::cout
        << "[BoxMoverPlugin] Primera salchicha detectada."
        << std::endl;

      std::cout
        << "[BoxMoverPlugin] Iniciando cinta a "
        << BELT_SPEED
        << " m/s."
        << std::endl;
    }


    // ==========================================================
    // CINTA FUNCIONANDO
    // ==========================================================

    if (started && !stopped)
    {
      const double elapsedTime =
        simTime - startTime;


      // --------------------------------------------------------
      // TODAVÍA TIENE QUE MOVERSE
      // --------------------------------------------------------

      if (elapsedTime < STOP_TIME)
      {
        // PUBLICAMOS CONTINUAMENTE
        SetBeltSpeed(BELT_SPEED);
      }


      // --------------------------------------------------------
      // TIEMPO TERMINADO
      // --------------------------------------------------------

      else
      {
        stopped = true;

        SetBeltSpeed(0.0);

        std::cout
          << "[BoxMoverPlugin] Han pasado "
          << STOP_TIME
          << " segundos."
          << std::endl;

        std::cout
          << "[BoxMoverPlugin] Cinta detenida."
          << std::endl;
      }
    }
  }


  // ============================================================
  // CAMBIAR VELOCIDAD
  // ============================================================

  void SetBeltSpeed(double speed)
  {
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

}  // namespace box_mover


// ================================================================
// REGISTRO DEL PLUGIN
// ================================================================

GZ_ADD_PLUGIN(
  box_mover::BoxMoverPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(
  box_mover::BoxMoverPlugin,
  "box_mover::BoxMoverPlugin")