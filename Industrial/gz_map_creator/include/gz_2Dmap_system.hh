/*
 * Copyright 2015 Fadri Furrer, ASL, ETH Zurich, Switzerland
 * Copyright 2015 Michael Burri, ASL, ETH Zurich, Switzerland
 * Copyright 2015 Mina Kamel, ASL, ETH Zurich, Switzerland
 * Copyright 2015 Janosch Nikolic, ASL, ETH Zurich, Switzerland
 * Copyright 2015 Markus Achtelik, ASL, ETH Zurich, Switzerland
 * Copyright 2024 Gazebo Fortress port
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef GZ_2DMAP_SYSTEM_HH
#define GZ_2DMAP_SYSTEM_HH

#include <memory>
#include <string>
#include <vector>

// Ignition Fortress headers
#include <gz/sim/System.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/occupancy_grid.pb.h>
#include <gz/msgs/empty.pb.h>
#include <gz/math/AxisAlignedBox.hh>

// Compatibility namespace alias for Ignition Fortress
namespace gz_compat {
  namespace sim = gz::sim;
  namespace transport = gz::transport;
  namespace msgs = gz::msgs;
  namespace math = gz::math;
}

namespace gz_2dmap_plugin
{

/// \brief Gazebo Fortress (Ignition Gazebo) system plugin that generates 
///        2D occupancy maps from the simulated world at a configurable height.
///
/// This plugin uses the Entity-Component-System (ECS) architecture of
/// Ignition Gazebo and publishes occupancy grids via Ignition Transport.
/// Use ros_gz_bridge to bridge the /map2d topic to ROS 2.
///
/// ## Plugin Parameters
/// - map_resolution: Cell size in meters (default: 0.05)
/// - map_height: Height to slice world in meters (default: 0.2)
/// - map_size_x: Map width - omit for auto-detection
/// - map_size_y: Map height - omit for auto-detection
/// - map_margin: Extra space around auto-detected bounds (default: 2.0)
/// - init_robot_x: Starting X for exploration (default: 0.0)
/// - init_robot_y: Starting Y for exploration (default: 0.0)
///
/// ## Example SDF
/// ```xml
/// <plugin filename="gz_2Dmap_system" name="ignition::gazebo::systems::OccupancyMapFromWorld">
///   <map_resolution>0.05</map_resolution>
///   <map_height>0.3</map_height>
/// </plugin>
/// ```
class OccupancyMapFromWorld
    : public gz_compat::sim::System,
      public gz_compat::sim::ISystemConfigure,
      public gz_compat::sim::ISystemPostUpdate
{
public:
  /// \brief Constructor
  OccupancyMapFromWorld();

  /// \brief Destructor
  ~OccupancyMapFromWorld() override;

  // Documentation inherited
  void Configure(const gz_compat::sim::Entity &_entity,
                 const std::shared_ptr<const sdf::Element> &_sdf,
                 gz_compat::sim::EntityComponentManager &_ecm,
                 gz_compat::sim::EventManager &_eventMgr) override;

  // Documentation inherited
  void PostUpdate(const gz_compat::sim::UpdateInfo &_info,
                  const gz_compat::sim::EntityComponentManager &_ecm) override;

private:
  /// \brief Compute world bounding box from all models
  /// \param[in] _ecm Entity component manager
  /// \param[out] minX Minimum x coordinate
  /// \param[out] maxX Maximum x coordinate
  /// \param[out] minY Minimum y coordinate
  /// \param[out] maxY Maximum y coordinate
  /// \return true if bounding box was computed successfully
  bool ComputeWorldBounds(const gz_compat::sim::EntityComponentManager &_ecm,
                          double &minX, double &maxX,
                          double &minY, double &maxY);

  /// \brief Create the occupancy map using collision detection
  /// \param[in] _ecm Entity component manager for geometry queries
  void CreateOccupancyMap(const gz_compat::sim::EntityComponentManager &_ecm);

  /// \brief Check if a cell intersects with world geometry
  /// \param[in] cellCenter Center of the cell
  /// \param[in] cellLength Size of the cell
  /// \param[in] _ecm Entity component manager
  /// \return true if cell is occupied
  bool WorldCellIntersection(const gz_compat::math::Vector3d &cellCenter,
                             double cellLength,
                             const gz_compat::sim::EntityComponentManager &_ecm);

  /// \brief Convert cell coordinates to world coordinates
  void Cell2World(unsigned int cellX, unsigned int cellY,
                  double &worldX, double &worldY);

  /// \brief Convert world coordinates to cell coordinates
  void World2Cell(double worldX, double worldY,
                  unsigned int &cellX, unsigned int &cellY);

  /// \brief Convert cell coordinates to map index
  bool Cell2Index(int cellX, int cellY, unsigned int &mapIndex);

  /// \brief Convert map index to cell coordinates
  bool Index2Cell(int index, unsigned int &cellX, unsigned int &cellY);

  /// \brief Service callback for map generation
  bool OnGenerateMap(const gz_compat::msgs::Empty &_req, gz_compat::msgs::Empty &_rep);

  /// \brief Publish the occupancy map
  void PublishMap();

  /// \brief Save map to PGM and YAML files
  /// \param[in] basePath Base path for output files (without extension)
  void SaveMapToFiles(const std::string &basePath);

private:
  /// \brief Ignition transport node
  gz_compat::transport::Node node_;

  /// \brief Publisher for occupancy grid
  gz_compat::transport::Node::Publisher mapPub_;

  /// \brief World entity
  gz_compat::sim::Entity worldEntity_{gz_compat::sim::kNullEntity};

  /// \brief Plugin name for logging
  std::string name_{"gz_2Dmap_plugin"};

  /// \brief Map resolution in meters per cell
  double mapResolution_{0.05};

  /// \brief Height at which to slice the world
  double mapHeight_{0.2};

  /// \brief Map size in X direction (meters)
  double mapSizeX_{10.0};

  /// \brief Map size in Y direction (meters)
  double mapSizeY_{10.0};

  /// \brief Initial robot X position for wavefront expansion
  double initRobotX_{0.0};

  /// \brief Initial robot Y position for wavefront expansion
  double initRobotY_{0.0};

  /// \brief Margin around auto-detected bounds
  double mapMargin_{2.0};

  /// \brief Map origin X (center of map)
  double mapOriginX_{0.0};

  /// \brief Map origin Y (center of map)
  double mapOriginY_{0.0};

  /// \brief Number of cells in X direction
  unsigned int cellsSizeX_{0};

  /// \brief Number of cells in Y direction
  unsigned int cellsSizeY_{0};

  /// \brief Whether map size was manually specified
  bool mapSizeXSpecified_{false};
  bool mapSizeYSpecified_{false};

  /// \brief Flag indicating map generation is requested
  bool generateMapRequested_{false};

  /// \brief Flag indicating the plugin has been configured
  bool configured_{false};

  /// \brief The occupancy map data
  std::vector<int8_t> occupancyData_;

  /// \brief Pointer to ECM for use in callbacks (set during PostUpdate)
  const gz_compat::sim::EntityComponentManager *ecmPtr_{nullptr};

  /// \brief Output path for saving map files (without extension)
  std::string outputPath_;
};

}  // namespace gz_2dmap_plugin

#endif  // GZ_2DMAP_SYSTEM_HH