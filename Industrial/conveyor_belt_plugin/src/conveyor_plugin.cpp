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

  static constexpr double BELT_SPEED = -0.5;

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
    (void)_sdf;
    (void)_eventMgr;

    // ----------------------------------------------------------
    // Obtener el nombre del modelo donde está cargado el plugin
    // ----------------------------------------------------------

    std::string modelName = "conveyor_belt";

    auto nameComp =
      _ecm.Component<gz::sim::components::Name>(_entity);

    if (nameComp)
    {
      modelName = nameComp->Data();
    }

    std::cout
      << "[BoxMoverPlugin] Modelo detectado: "
      << modelName
      << std::endl;


    // ----------------------------------------------------------
    // Construir dinámicamente el tópico del TrackController
    // ----------------------------------------------------------

    const std::string topic =
      "/model/" +
      modelName +
      "/link/link/track_cmd_vel";


    std::cout
      << "[BoxMoverPlugin] TrackController topic: "
      << topic
      << std::endl;


    // ----------------------------------------------------------
    // Crear publisher
    // ----------------------------------------------------------

    speedPublisher =
      transportNode.Advertise<gz::msgs::Double>(topic);


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
    if (stopped)
      return;


    const double simTime =
      _info.simTime.count();


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
        const std::string name =
          _name->Data();


        if (name.rfind("box_", 0) == 0)
        {
          sausageFound = true;

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
    // MANTENER VELOCIDAD
    // ==========================================================

    if (started && !stopped)
    {
      SetBeltSpeed(BELT_SPEED);


      const double elapsedTime =
        simTime - startTime;


      if (elapsedTime >= STOP_TIME)
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
  // VELOCIDAD DE LA CINTA
  // ============================================================

  void SetBeltSpeed(double speed)
  {
    if (!speedPublisher)
      return;


    gz::msgs::Double msg;

    msg.set_data(speed);

    speedPublisher.Publish(msg);
  }
};

}  // namespace box_mover


// ================================================================
// REGISTRO
// ================================================================

GZ_ADD_PLUGIN(
  box_mover::BoxMoverPlugin,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(
  box_mover::BoxMoverPlugin,
  "box_mover::BoxMoverPlugin")