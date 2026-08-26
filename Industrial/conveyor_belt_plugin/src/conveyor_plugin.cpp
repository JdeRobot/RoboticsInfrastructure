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

  // Velocidad de la superficie de la cinta.
  //
  // La cinta se desplaza en dirección -Y.
  static constexpr double BELT_SPEED = -0.15;

  // Tiempo que la cinta permanece funcionando
  // desde que aparece la primera salchicha.
  static constexpr double STOP_TIME = 10.0;


  // ============================================================
  // ESTADO
  // ============================================================

  // Se ha detectado al menos una salchicha.
  bool started = false;

  // El TrackController ya está conectado
  // al publisher.
  bool beltStarted = false;

  // La cinta ya se ha detenido.
  bool stopped = false;

  // Tiempo de simulación en el que apareció
  // la primera salchicha.
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

    // ==========================================================
    // TÓPICO DEL TRACK CONTROLLER
    // ==========================================================
    //
    // El modelo incluido en el mundo se llama:
    //
    // conveyor_belt_1
    //
    // y contiene:
    //
    // link -> link
    //
    // Por tanto:
    //
    // /model/conveyor_belt_1/link/link/track_cmd_vel
    //

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


  // ============================================================
  // PREUPDATE
  // ============================================================

  void PreUpdate(
    const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager &_ecm) override
  {
    // Tiempo actual de simulación.
    const double simTime = _info.simTime.count();


    // ==========================================================
    // SI YA SE HA DETENIDO
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


        // Las salchichas se llaman:
        //
        // box_0
        // box_1
        // box_2
        // box_3
        //

        if (name.find("box_") != std::string::npos)
        {
          sausageFound = true;

          // Ya hemos encontrado una.
          return false;
        }


        return true;
      });


    // ==========================================================
    // PRIMERA SALCHICHA DETECTADA
    // ==========================================================

    if (sausageFound && !started)
    {
      started = true;

      // Guardamos el instante exacto en el que
      // aparece la primera salchicha.
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


    // ==========================================================
    // ESPERAR A QUE TRACK CONTROLLER ESTÉ CONECTADO
    // ==========================================================

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


        // Primer comando de velocidad.
        SetBeltSpeed(BELT_SPEED);
      }
    }


    // ==========================================================
    // CINTA EN FUNCIONAMIENTO
    // ==========================================================

    if (started && beltStarted && !stopped)
    {
      const double elapsedTime =
        simTime - startTime;


      // ========================================================
      // TODAVÍA NO HA LLEGADO EL MOMENTO DE PARAR
      // ========================================================

      if (elapsedTime < STOP_TIME)
      {
        // No necesitamos publicar continuamente.
        //
        // TrackController mantiene la velocidad que se le
        // ha enviado.
      }


      // ========================================================
      // HA PASADO EL TIEMPO
      // ========================================================

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


        // Detener TrackController.
        SetBeltSpeed(0.0);
      }
    }
  }


  // ============================================================
  // PUBLICAR VELOCIDAD AL TRACK CONTROLLER
  // ============================================================

  void SetBeltSpeed(double speed)
  {
    std::cout
      << "[BoxMoverPlugin] SetBeltSpeed("
      << speed
      << ")"
      << std::endl;


    // Comprobar si el publisher está conectado.
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


    // Crear mensaje.
    gz::msgs::Double msg;

    msg.set_data(speed);


    // Publicar.
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