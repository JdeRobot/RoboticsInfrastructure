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
  //
  // Negativa porque queremos mover las salchichas
  // en dirección -Y.
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

    // Tópico por defecto del TrackController:
    //
    // /model/conveyor_belt/link/link/track_cmd_vel
    //
    speedPublisher =
      transportNode.Advertise<gz::msgs::Double>(
        "/model/conveyor_belt/link/link/track_cmd_vel");


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
        << "[BoxMoverPlugin] TrackController publisher creado."
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
    // Si ya hemos parado la cinta no hacemos nada.
    if (stopped)
      return;


    // Tiempo actual de simulación.
    const double simTime = _info.simTime.count();


    // ==========================================================
    // BUSCAR PRIMERA SALCHICHA
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


        // Solo nos interesan:
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
          // No necesitamos seguir buscando.
          return false;
        }


        return true;
      });


    // ==========================================================
    // APARECE LA PRIMERA SALCHICHA
    // ==========================================================

    if (sausageFound && !started)
    {
      started = true;

      // Guardamos el instante en el que apareció
      // la primera salchicha.
      startTime = simTime;


      // Arrancamos la cinta.
      SetBeltSpeed(BELT_SPEED);


      std::cout
        << "[BoxMoverPlugin] Primera salchicha detectada."
        << std::endl;

      std::cout
        << "[BoxMoverPlugin] Cinta arrancada a "
        << BELT_SPEED
        << " m/s."
        << std::endl;
    }


    // ==========================================================
    // COMPROBAR TIEMPO
    // ==========================================================

    if (started && !stopped)
    {
      const double elapsedTime =
        simTime - startTime;


      if (elapsedTime >= STOP_TIME)
      {
        stopped = true;


        // Detener la cinta.
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
  // CAMBIAR VELOCIDAD DEL TRACK CONTROLLER
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
  gz::sim::System::ISystemConfigure,
  gz::sim::System::ISystemPreUpdate)


GZ_ADD_PLUGIN_ALIAS(
  box_mover::BoxMoverPlugin,
  "box_mover::BoxMoverPlugin")