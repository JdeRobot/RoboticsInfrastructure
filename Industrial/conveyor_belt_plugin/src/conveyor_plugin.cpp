#include <gz/sim/System.hh>

#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Pose.hh>

#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/double.pb.h>
#include <gz/sim/System.hh>

namespace box_mover
{

class BoxMoverPlugin:
  public gz::sim::System,
  public gz::sim::ISystemConfigure,
  public gz::sim::ISystemPreUpdate
{
public:

  // ============================================================
  // CONFIGURACIÓN
  // ============================================================

  // Velocidad de la cinta.
  // Negativa porque la cinta se mueve en dirección -Y.
  static constexpr double BELT_SPEED = -0.15;

  // Tiempo que la cinta permanece funcionando desde
  // que aparece la primera salchicha.
  static constexpr double STOP_TIME = 10.0;

  // ============================================================
  // VARIABLES DE ESTADO
  // ============================================================

  // Indica si ya ha aparecido la primera salchicha.
  bool started = false;

  // Indica si la cinta ya ha sido detenida.
  bool stopped = false;

  // Tiempo de simulación en el que apareció la primera salchicha.
  double startTime = 0.0;

  // Nodo de Gazebo Transport.
  gz::transport::Node transportNode;

  // Publisher para controlar TrackController.
  gz::transport::Node::Publisher speedPublisher;


  // ============================================================
  // CONFIGURACIÓN DEL PLUGIN
  // ============================================================

  void Configure(
    const gz::sim::Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &_ecm,
    gz::sim::EventManager &_eventMgr) override
  {
    // El TrackController del modelo conveyor_belt/link
    // recibe comandos en este tópico.
    speedPublisher =
      transportNode.Advertise<gz::msgs::Double>(
        "/model/conveyor_belt/link/link/track_cmd_vel");

    if (!speedPublisher)
    {
      std::cerr
        << "[BoxMoverPlugin] ERROR: no se pudo crear "
        << "el publisher de velocidad de la cinta."
        << std::endl;
    }
    else
    {
      std::cout
        << "[BoxMoverPlugin] Publisher de TrackController creado."
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

    // ------------------------------------------------------------
    // Si la cinta ya está parada, no hacemos nada más.
    // ------------------------------------------------------------

    if (stopped)
      return;


    // ------------------------------------------------------------
    // Buscar salchichas
    // ------------------------------------------------------------

    bool sausageFound = false;

    _ecm.Each<
      gz::sim::components::Model,
      gz::sim::components::Name,
      gz::sim::components::Pose>(
      [&](const gz::sim::Entity &,
          const gz::sim::components::Model *,
          const gz::sim::components::Name *_name,
          const gz::sim::components::Pose *)->bool
      {
        const std::string name = _name->Data();

        // Solamente nos interesan los modelos box_0,
        // box_1, box_2, box_3, etc.
        if (name.find("box_") == std::string::npos)
          return true;

        sausageFound = true;

        return false;
      });


    // ------------------------------------------------------------
    // PRIMERA SALCHICHA
    // ------------------------------------------------------------

    if (sausageFound && !started)
    {
      started = true;

      // Guardamos el instante exacto en el que apareció
      // la primera salchicha.
      startTime = simTime;

      // Arrancar la cinta.
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


    // ------------------------------------------------------------
    // PARADA DE LA CINTA
    // ------------------------------------------------------------

    if (started)
    {
      const double elapsedTime = simTime - startTime;

      if (elapsedTime >= STOP_TIME)
      {
        stopped = true;

        // Detener TrackController.
        SetBeltSpeed(0.0);

        std::cout
          << "[BoxMoverPlugin] Han pasado "
          << STOP_TIME
          << " segundos desde la primera salchicha."
          << std::endl;

        std::cout
          << "[BoxMoverPlugin] Cinta detenida."
          << std::endl;
      }
    }
  }


  // ============================================================
  // CAMBIAR VELOCIDAD DE LA CINTA
  // ============================================================

  void SetBeltSpeed(double speed)
  {
    if (!speedPublisher)
      return;

    gz::msgs::Double msg;

    msg.set_data(speed);

    speedPublisher.Publish(msg);

    std::cout
      << "[BoxMoverPlugin] Belt speed -> "
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
  box_mover::BoxMoverPlugin::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(
  box_mover::BoxMoverPlugin,
  "box_mover::BoxMoverPlugin")