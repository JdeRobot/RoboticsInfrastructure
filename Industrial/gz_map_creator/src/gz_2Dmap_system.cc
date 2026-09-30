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

#include "gz_2Dmap_system.hh"

#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <limits>
#include <queue>

// Use ignition naming for Fortress
#include <gz/plugin/Register.hh>
#include <gz/sim/World.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Collision.hh>
#include <gz/sim/components/Geometry.hh>
#include <gz/sim/components/World.hh>
#include <gz/sim/Util.hh>
#include <gz/common/Console.hh>
#include <gz/math/Vector3.hh>

// SDF headers for geometry shapes
#include <sdf/Box.hh>
#include <sdf/Cylinder.hh>
#include <sdf/Sphere.hh>
#include <sdf/Mesh.hh>
#include <sdf/Plane.hh>

namespace gz_2dmap_plugin
{

// Namespace aliases for Ignition Fortress
namespace sim = gz::sim;
namespace math = gz::math;

//////////////////////////////////////////////////
OccupancyMapFromWorld::OccupancyMapFromWorld()
{
  ignmsg << "[" << name_ << "] Occupancy map plugin started" << std::endl;
}

//////////////////////////////////////////////////
OccupancyMapFromWorld::~OccupancyMapFromWorld()
{
}

//////////////////////////////////////////////////
void OccupancyMapFromWorld::Configure(
    const gz_compat::sim::Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz_compat::sim::EntityComponentManager &_ecm,
    gz_compat::sim::EventManager &/*_eventMgr*/)
{
  worldEntity_ = _entity;

  // Get map resolution
  if (_sdf->HasElement("map_resolution"))
  {
    mapResolution_ = _sdf->Get<double>("map_resolution");
  }
  ignmsg << "[" << name_ << "] Map resolution: " << mapResolution_ << std::endl;

  // Get map height (z-level for slicing)
  if (_sdf->HasElement("map_height"))
  {
    mapHeight_ = _sdf->Get<double>("map_height");
  }
  else if (_sdf->HasElement("map_z"))
  {
    mapHeight_ = _sdf->Get<double>("map_z");
  }
  ignmsg << "[" << name_ << "] Map height: " << mapHeight_ << std::endl;

  // Get initial robot position
  if (_sdf->HasElement("init_robot_x"))
  {
    initRobotX_ = _sdf->Get<double>("init_robot_x");
  }
  if (_sdf->HasElement("init_robot_y"))
  {
    initRobotY_ = _sdf->Get<double>("init_robot_y");
  }
  ignmsg << "[" << name_ << "] Init position: (" << initRobotX_ << ", " 
        << initRobotY_ << ")" << std::endl;

  // Get map margin
  if (_sdf->HasElement("map_margin"))
  {
    mapMargin_ = _sdf->Get<double>("map_margin");
  }

  // Check if map sizes are manually specified
  mapSizeXSpecified_ = _sdf->HasElement("map_size_x");
  mapSizeYSpecified_ = _sdf->HasElement("map_size_y");

  if (mapSizeXSpecified_)
  {
    mapSizeX_ = _sdf->Get<double>("map_size_x");
  }
  if (mapSizeYSpecified_)
  {
    mapSizeY_ = _sdf->Get<double>("map_size_y");
  }

  // If sizes not specified, try to auto-detect from world bounds
  if (!mapSizeXSpecified_ || !mapSizeYSpecified_)
  {
    double minX, maxX, minY, maxY;
    if (ComputeWorldBounds(_ecm, minX, maxX, minY, maxY))
    {
      if (!mapSizeXSpecified_)
      {
        double maxExtentX = std::max(std::abs(minX), std::abs(maxX));
        mapSizeX_ = 2.0 * maxExtentX + 2.0 * mapMargin_;
        mapOriginX_ = 0.0;
        ignmsg << "[" << name_ << "] Auto-detected map_size_x: " << mapSizeX_
              << " (world bounds: " << minX << " to " << maxX << ")" << std::endl;
      }

      if (!mapSizeYSpecified_)
      {
        double maxExtentY = std::max(std::abs(minY), std::abs(maxY));
        mapSizeY_ = 2.0 * maxExtentY + 2.0 * mapMargin_;
        mapOriginY_ = 0.0;
        ignmsg << "[" << name_ << "] Auto-detected map_size_y: " << mapSizeY_
              << " (world bounds: " << minY << " to " << maxY << ")" << std::endl;
      }
    }
    else
    {
      ignwarn << "[" << name_ << "] Failed to auto-detect world bounds. "
             << "Using default values." << std::endl;
    }
  }

  // Calculate cell counts
  cellsSizeX_ = static_cast<unsigned int>(mapSizeX_ / mapResolution_);
  cellsSizeY_ = static_cast<unsigned int>(mapSizeY_ / mapResolution_);

  ignmsg << "[" << name_ << "] Map configuration - Size: " << mapSizeX_ << "x" 
        << mapSizeY_ << ", Cells: " << cellsSizeX_ << "x" << cellsSizeY_ << std::endl;

  // Initialize Gazebo transport
  std::string mapTopic = "/map2d";
  mapPub_ = node_.Advertise<gz_compat::msgs::OccupancyGrid>(mapTopic);
  ignmsg << "[" << name_ << "] Publishing map on: " << mapTopic << std::endl;

  // Advertise the generate_map service
  std::string serviceName = "/gazebo_2Dmap_plugin/generate_map";
  node_.Advertise(serviceName, &OccupancyMapFromWorld::OnGenerateMap, this);
  ignmsg << "[" << name_ << "] Service available: " << serviceName << std::endl;

  // Get output path for saving map files directly
  if (_sdf->HasElement("output_path"))
  {
    outputPath_ = _sdf->Get<std::string>("output_path");
    ignmsg << "[" << name_ << "] Will save map to: " << outputPath_ << std::endl;
  }

  configured_ = true;
}

//////////////////////////////////////////////////
void OccupancyMapFromWorld::PostUpdate(
    const gz_compat::sim::UpdateInfo &/*_info*/,
    const gz_compat::sim::EntityComponentManager &_ecm)
{
  if (!configured_)
    return;

  // Store ECM pointer for use in map generation
  ecmPtr_ = &_ecm;

  // Check if map generation was requested
  if (generateMapRequested_)
  {
    generateMapRequested_ = false;
    
    // Recompute world bounds now that models should be fully loaded
    if (!mapSizeXSpecified_ || !mapSizeYSpecified_)
    {
      double minX, maxX, minY, maxY;
      if (ComputeWorldBounds(_ecm, minX, maxX, minY, maxY))
      {
        if (!mapSizeXSpecified_)
        {
          double maxExtentX = std::max(std::abs(minX), std::abs(maxX));
          mapSizeX_ = 2.0 * maxExtentX + 2.0 * mapMargin_;
          ignmsg << "[" << name_ << "] Auto-detected map_size_x: " << mapSizeX_
                << " (bounds: " << minX << " to " << maxX << ")" << std::endl;
        }
        if (!mapSizeYSpecified_)
        {
          double maxExtentY = std::max(std::abs(minY), std::abs(maxY));
          mapSizeY_ = 2.0 * maxExtentY + 2.0 * mapMargin_;
          ignmsg << "[" << name_ << "] Auto-detected map_size_y: " << mapSizeY_
                << " (bounds: " << minY << " to " << maxY << ")" << std::endl;
        }
        // Recalculate cell counts
        cellsSizeX_ = static_cast<unsigned int>(mapSizeX_ / mapResolution_);
        cellsSizeY_ = static_cast<unsigned int>(mapSizeY_ / mapResolution_);
        ignmsg << "[" << name_ << "] Map cells: " << cellsSizeX_ << "x" << cellsSizeY_ << std::endl;
      }
    }
    
    CreateOccupancyMap(_ecm);
    PublishMap();
    
    // Save map files if output path is specified
    if (!outputPath_.empty())
    {
      SaveMapToFiles(outputPath_);
    }
  }
}

//////////////////////////////////////////////////
bool OccupancyMapFromWorld::OnGenerateMap(
    const gz_compat::msgs::Empty &/*_req*/,
    gz_compat::msgs::Empty &/*_rep*/)
{
  ignmsg << "[" << name_ << "] Map generation requested" << std::endl;
  generateMapRequested_ = true;
  return true;
}

//////////////////////////////////////////////////
bool OccupancyMapFromWorld::ComputeWorldBounds(
    const gz_compat::sim::EntityComponentManager &_ecm,
    double &minX, double &maxX,
    double &minY, double &maxY)
{
  bool boundsInitialized = false;
  minX = minY = 0.0;
  maxX = maxY = 0.0;
  int modelCount = 0;

  // Get the world
  sim::World world(worldEntity_);
  
  // Iterate through all models
  _ecm.Each<sim::components::Model,
            sim::components::Name,
            sim::components::Pose>(
    [&](const gz_compat::sim::Entity &_entity,
        const sim::components::Model *,
        const sim::components::Name *_name,
        const sim::components::Pose *) -> bool
    {
      sim::Model model(_entity);
      
      // Get world pose
      auto worldPose = sim::worldPose(_entity, _ecm);
      
      // Get model bounding box by checking its collision geometries
      double modelMinX = worldPose.Pos().X();
      double modelMaxX = worldPose.Pos().X();
      double modelMinY = worldPose.Pos().Y();
      double modelMaxY = worldPose.Pos().Y();
      
      // Try to get better bounds from collision geometries
      auto links = model.Links(_ecm);
      for (const auto &linkEntity : links)
      {
        sim::Link link(linkEntity);
        auto collisions = link.Collisions(_ecm);
        
        for (const auto &collisionEntity : collisions)
        {
          auto *geometry = _ecm.Component<sim::components::Geometry>(collisionEntity);
          if (geometry)
          {
            // Get collision pose in world frame
            auto collisionWorldPose = sim::worldPose(collisionEntity, _ecm);
            
            // Estimate bounds based on geometry type
            const sdf::Geometry &geom = geometry->Data();
            double extentX = 1.0, extentY = 1.0;
            
            if (geom.Type() == sdf::GeometryType::BOX && geom.BoxShape())
            {
              extentX = geom.BoxShape()->Size().X() / 2.0;
              extentY = geom.BoxShape()->Size().Y() / 2.0;
            }
            else if (geom.Type() == sdf::GeometryType::CYLINDER && geom.CylinderShape())
            {
              extentX = geom.CylinderShape()->Radius();
              extentY = geom.CylinderShape()->Radius();
            }
            else if (geom.Type() == sdf::GeometryType::SPHERE && geom.SphereShape())
            {
              extentX = geom.SphereShape()->Radius();
              extentY = geom.SphereShape()->Radius();
            }
            else if (geom.Type() == sdf::GeometryType::PLANE)
            {
              // Planes are typically ground planes, use a large default
              extentX = 50.0;
              extentY = 50.0;
            }
            else if (geom.Type() == sdf::GeometryType::MESH && geom.MeshShape())
            {
              // For meshes, use scale as a rough estimate
              auto scale = geom.MeshShape()->Scale();
              extentX = scale.X();
              extentY = scale.Y();
            }
            
            modelMinX = std::min(modelMinX, collisionWorldPose.Pos().X() - extentX);
            modelMaxX = std::max(modelMaxX, collisionWorldPose.Pos().X() + extentX);
            modelMinY = std::min(modelMinY, collisionWorldPose.Pos().Y() - extentY);
            modelMaxY = std::max(modelMaxY, collisionWorldPose.Pos().Y() + extentY);
          }
        }
      }

      if (!boundsInitialized)
      {
        minX = modelMinX;
        maxX = modelMaxX;
        minY = modelMinY;
        maxY = modelMaxY;
        boundsInitialized = true;
      }
      else
      {
        minX = std::min(minX, modelMinX);
        maxX = std::max(maxX, modelMaxX);
        minY = std::min(minY, modelMinY);
        maxY = std::max(maxY, modelMaxY);
      }

      modelCount++;
      igndbg << "[" << name_ << "] Model '" << _name->Data() 
            << "': X[" << modelMinX << ", " << modelMaxX 
            << "], Y[" << modelMinY << ", " << modelMaxY << "]" << std::endl;

      return true;  // Continue iteration
    });

  if (modelCount > 0 && boundsInitialized)
  {
    ignmsg << "[" << name_ << "] Computed world bounds from " << modelCount 
          << " models: X[" << minX << ", " << maxX 
          << "], Y[" << minY << ", " << maxY << "]" << std::endl;
    return true;
  }

  ignwarn << "[" << name_ << "] No valid bounding boxes found" << std::endl;
  return false;
}

//////////////////////////////////////////////////
void OccupancyMapFromWorld::Cell2World(
    unsigned int cellX, unsigned int cellY,
    double &worldX, double &worldY)
{
  worldX = mapOriginX_ - mapSizeX_/2 + cellX * mapResolution_ + mapResolution_/2;
  worldY = mapOriginY_ - mapSizeY_/2 + cellY * mapResolution_ + mapResolution_/2;
}

//////////////////////////////////////////////////
void OccupancyMapFromWorld::World2Cell(
    double worldX, double worldY,
    unsigned int &cellX, unsigned int &cellY)
{
  cellX = static_cast<unsigned int>((worldX - mapOriginX_ + mapSizeX_/2) / mapResolution_);
  cellY = static_cast<unsigned int>((worldY - mapOriginY_ + mapSizeY_/2) / mapResolution_);
}

//////////////////////////////////////////////////
bool OccupancyMapFromWorld::Cell2Index(
    int cellX, int cellY, unsigned int &mapIndex)
{
  if (cellX >= 0 && static_cast<unsigned int>(cellX) < cellsSizeX_ &&
      cellY >= 0 && static_cast<unsigned int>(cellY) < cellsSizeY_)
  {
    mapIndex = cellY * cellsSizeX_ + cellX;
    return true;
  }
  return false;
}

//////////////////////////////////////////////////
bool OccupancyMapFromWorld::Index2Cell(
    int index, unsigned int &cellX, unsigned int &cellY)
{
  cellY = index / cellsSizeX_;
  cellX = index % cellsSizeX_;
  return (cellX < cellsSizeX_ && cellY < cellsSizeY_);
}

//////////////////////////////////////////////////
bool OccupancyMapFromWorld::WorldCellIntersection(
    const gz_compat::math::Vector3d &cellCenter,
    double cellLength,
    const gz_compat::sim::EntityComponentManager &_ecm)
{
  // Check AABB overlap with all collision geometries
  double halfCell = cellLength / 2.0;
  math::AxisAlignedBox cellBox(
      math::Vector3d(cellCenter.X() - halfCell, cellCenter.Y() - halfCell, cellCenter.Z() - 0.1),
      math::Vector3d(cellCenter.X() + halfCell, cellCenter.Y() + halfCell, cellCenter.Z() + 0.1));
  
  bool occupied = false;
  
  _ecm.Each<sim::components::Collision,
            sim::components::Geometry>(
    [&](const gz_compat::sim::Entity &collisionEntity,
        const sim::components::Collision *,
        const sim::components::Geometry *geometry) -> bool
    {
      if (occupied) return false;  // Already found intersection
      
      auto collisionPose = sim::worldPose(collisionEntity, _ecm);
      const sdf::Geometry &geom = geometry->Data();
      
      // Skip plane geometries (ground planes) - they should not block movement
      if (geom.Type() == sdf::GeometryType::PLANE)
      {
        return true;  // Continue to next collision
      }
      
      // Create AABB for the collision geometry
      math::Vector3d extents(0.5, 0.5, 0.5);  // Default
      
      if (geom.Type() == sdf::GeometryType::BOX && geom.BoxShape())
      {
        extents = geom.BoxShape()->Size() / 2.0;
      }
      else if (geom.Type() == sdf::GeometryType::CYLINDER && geom.CylinderShape())
      {
        double r = geom.CylinderShape()->Radius();
        double h = geom.CylinderShape()->Length();
        extents = math::Vector3d(r, r, h/2.0);
      }
      else if (geom.Type() == sdf::GeometryType::SPHERE && geom.SphereShape())
      {
        double r = geom.SphereShape()->Radius();
        extents = math::Vector3d(r, r, r);
      }
      else if (geom.Type() == sdf::GeometryType::MESH && geom.MeshShape())
      {
        // Mesh scale is typically (1,1,1) - use a reasonable default based on scale
        auto scale = geom.MeshShape()->Scale();
        // Use scale as a multiplier on a base 1m size estimate
        extents = math::Vector3d(scale.X() * 0.5, scale.Y() * 0.5, scale.Z() * 0.5);
        // Ensure minimum size
        if (extents.X() < 0.1) extents.X() = 0.5;
        if (extents.Y() < 0.1) extents.Y() = 0.5;
        if (extents.Z() < 0.1) extents.Z() = 0.5;
      }
      
      // Compute rotated AABB for box geometries
      // For boxes that are rotated, we need to transform the corners
      // and find the actual axis-aligned bounds
      math::AxisAlignedBox collisionBox;
      
      if (geom.Type() == sdf::GeometryType::BOX && geom.BoxShape())
      {
        // Get the 8 corners of the box in local frame
        math::Vector3d halfSize = geom.BoxShape()->Size() / 2.0;
        std::array<math::Vector3d, 8> corners = {{
          math::Vector3d(-halfSize.X(), -halfSize.Y(), -halfSize.Z()),
          math::Vector3d( halfSize.X(), -halfSize.Y(), -halfSize.Z()),
          math::Vector3d(-halfSize.X(),  halfSize.Y(), -halfSize.Z()),
          math::Vector3d( halfSize.X(),  halfSize.Y(), -halfSize.Z()),
          math::Vector3d(-halfSize.X(), -halfSize.Y(),  halfSize.Z()),
          math::Vector3d( halfSize.X(), -halfSize.Y(),  halfSize.Z()),
          math::Vector3d(-halfSize.X(),  halfSize.Y(),  halfSize.Z()),
          math::Vector3d( halfSize.X(),  halfSize.Y(),  halfSize.Z())
        }};
        
        // Transform corners to world frame and find AABB
        math::Vector3d minPt(std::numeric_limits<double>::max(),
                             std::numeric_limits<double>::max(),
                             std::numeric_limits<double>::max());
        math::Vector3d maxPt(std::numeric_limits<double>::lowest(),
                             std::numeric_limits<double>::lowest(),
                             std::numeric_limits<double>::lowest());
        
        for (const auto& corner : corners)
        {
          math::Vector3d worldCorner = collisionPose.CoordPositionAdd(corner);
          minPt.X() = std::min(minPt.X(), worldCorner.X());
          minPt.Y() = std::min(minPt.Y(), worldCorner.Y());
          minPt.Z() = std::min(minPt.Z(), worldCorner.Z());
          maxPt.X() = std::max(maxPt.X(), worldCorner.X());
          maxPt.Y() = std::max(maxPt.Y(), worldCorner.Y());
          maxPt.Z() = std::max(maxPt.Z(), worldCorner.Z());
        }
        
        collisionBox = math::AxisAlignedBox(minPt, maxPt);
      }
      else
      {
        // For non-box geometries, use the simple approach
        collisionBox = math::AxisAlignedBox(
            collisionPose.Pos() - extents,
            collisionPose.Pos() + extents);
      }
      
      // Check if the collision geometry overlaps with the cell at map height
      if (collisionBox.Min().Z() <= cellCenter.Z() && 
          collisionBox.Max().Z() >= cellCenter.Z())
      {
        // Check 2D overlap
        if (collisionBox.Min().X() <= cellBox.Max().X() &&
            collisionBox.Max().X() >= cellBox.Min().X() &&
            collisionBox.Min().Y() <= cellBox.Max().Y() &&
            collisionBox.Max().Y() >= cellBox.Min().Y())
        {
          occupied = true;
          return false;  // Stop iteration
        }
      }
      
      return true;  // Continue iteration
    });
  
  return occupied;
}

//////////////////////////////////////////////////
void OccupancyMapFromWorld::CreateOccupancyMap(
    const gz_compat::sim::EntityComponentManager &_ecm)
{
  ignmsg << "[" << name_ << "] Starting wavefront expansion for mapping" << std::endl;

  // Initialize occupancy data
  occupancyData_.resize(cellsSizeX_ * cellsSizeY_);
  std::fill(occupancyData_.begin(), occupancyData_.end(), -1);  // Unknown

  // Find initial robot cell
  unsigned int cellX, cellY, mapIndex;
  World2Cell(initRobotX_, initRobotY_, cellX, cellY);

  if (!Cell2Index(cellX, cellY, mapIndex))
  {
    ignerr << "[" << name_ << "] Initial robot position (" << initRobotX_ 
          << ", " << initRobotY_ << ") is outside map bounds" << std::endl;
    return;
  }

  // Wavefront expansion
  std::queue<unsigned int> wavefront;
  wavefront.push(mapIndex);

  while (!wavefront.empty())
  {
    mapIndex = wavefront.front();
    wavefront.pop();

    Index2Cell(mapIndex, cellX, cellY);

    // Mark cell as free
    occupancyData_[mapIndex] = 0;

    // Explore 8-connected neighbors
    for (int i = -1; i < 2; i++)
    {
      for (int j = -1; j < 2; j++)
      {
        if (i == 0 && j == 0) continue;

        unsigned int childIndex;
        if (Cell2Index(cellX + i, cellY + j, childIndex))
        {
          int8_t childVal = occupancyData_[childIndex];

          // Only process unknown cells
          if (childVal != 100 && childVal != 0 && childVal != 50)
          {
            double worldX, worldY;
            Cell2World(cellX + i, cellY + j, worldX, worldY);

            math::Vector3d cellCenterPoint(worldX, worldY, mapHeight_);
            bool cellOccupied = WorldCellIntersection(cellCenterPoint, mapResolution_, _ecm);

            if (cellOccupied)
            {
              occupancyData_[childIndex] = 100;  // Occupied
            }
            else
            {
              wavefront.push(childIndex);
              occupancyData_[childIndex] = 50;  // In wavefront
            }
          }
        }
      }
    }
  }

  // Count statistics
  long freeCount = std::count(occupancyData_.begin(), occupancyData_.end(), 0);
  long occupiedCount = std::count(occupancyData_.begin(), occupancyData_.end(), 100);

  ignmsg << "[" << name_ << "] Map generation completed - Size: " << cellsSizeX_ 
        << "x" << cellsSizeY_ << ", Occupied: " << occupiedCount 
        << ", Free: " << freeCount << std::endl;
}

//////////////////////////////////////////////////
void OccupancyMapFromWorld::PublishMap()
{
  gz_compat::msgs::OccupancyGrid msg;

  // Set header
  auto *header = msg.mutable_header();
  auto *stamp = header->mutable_stamp();
  stamp->set_sec(0);
  stamp->set_nsec(0);
  
  // Add frame_id to header data
  auto *frameData = header->add_data();
  frameData->set_key("frame_id");
  frameData->add_value("odom");

  // Set map info
  auto *info = msg.mutable_info();
  info->set_width(cellsSizeX_);
  info->set_height(cellsSizeY_);
  info->set_resolution(mapResolution_);

  // Set origin
  auto *origin = info->mutable_origin();
  auto *position = origin->mutable_position();
  position->set_x(mapOriginX_ - mapSizeX_ / 2);
  position->set_y(mapOriginY_ - mapSizeY_ / 2);
  position->set_z(mapHeight_);
  
  auto *orientation = origin->mutable_orientation();
  orientation->set_w(1.0);
  orientation->set_x(0.0);
  orientation->set_y(0.0);
  orientation->set_z(0.0);

  // Set map data
  msg.set_data(occupancyData_.data(), occupancyData_.size());

  // Publish
  mapPub_.Publish(msg);
  
  ignmsg << "[" << name_ << "] Map published on /map2d topic" << std::endl;
}

//////////////////////////////////////////////////
void OccupancyMapFromWorld::SaveMapToFiles(const std::string &basePath)
{
  std::string pgmPath = basePath + ".pgm";
  std::string yamlPath = basePath + ".yaml";

  // Save PGM file
  std::ofstream pgmFile(pgmPath, std::ios::binary);
  if (!pgmFile.is_open())
  {
    ignerr << "[" << name_ << "] Failed to open PGM file: " << pgmPath << std::endl;
    return;
  }

  // Write PGM header (P5 binary format)
  pgmFile << "P5\n";
  pgmFile << cellsSizeX_ << " " << cellsSizeY_ << "\n";
  pgmFile << "255\n";

  // Write pixel data (flipped vertically for correct orientation)
  for (int y = static_cast<int>(cellsSizeY_) - 1; y >= 0; --y)
  {
    for (unsigned int x = 0; x < cellsSizeX_; ++x)
    {
      unsigned int idx = y * cellsSizeX_ + x;
      int8_t val = occupancyData_[idx];
      
      // Convert occupancy value to grayscale
      // -1 (unknown) -> 205 (gray)
      // 0 (free) -> 254 (white)  
      // 100 (occupied) -> 0 (black)
      unsigned char pixel;
      if (val == -1)
      {
        pixel = 205;  // Unknown - gray
      }
      else if (val == 0)
      {
        pixel = 254;  // Free - white
      }
      else
      {
        pixel = 0;  // Occupied - black
      }
      pgmFile.write(reinterpret_cast<char*>(&pixel), 1);
    }
  }
  pgmFile.close();

  // Save YAML file
  std::ofstream yamlFile(yamlPath);
  if (!yamlFile.is_open())
  {
    ignerr << "[" << name_ << "] Failed to open YAML file: " << yamlPath << std::endl;
    return;
  }

  // Get just the filename for the image reference
  size_t lastSlash = basePath.rfind('/');
  std::string mapName = (lastSlash != std::string::npos) 
      ? basePath.substr(lastSlash + 1) 
      : basePath;

  yamlFile << "image: " << mapName << ".pgm\n";
  yamlFile << "resolution: " << mapResolution_ << "\n";
  yamlFile << "origin: [" 
           << (mapOriginX_ - mapSizeX_ / 2) << ", " 
           << (mapOriginY_ - mapSizeY_ / 2) << ", 0.0]\n";
  yamlFile << "negate: 0\n";
  yamlFile << "occupied_thresh: 0.65\n";
  yamlFile << "free_thresh: 0.196\n";
  yamlFile.close();

  ignmsg << "[" << name_ << "] Map files saved: " << pgmPath << " and " << yamlPath << std::endl;
}

}  // namespace gz_2dmap_plugin

// Register the plugin for Ignition Fortress
// IGNITION_ADD_PLUGIN(
//     gz_2dmap_plugin::OccupancyMapFromWorld,
//     ignition::gazebo::System,
//     gz_2dmap_plugin::OccupancyMapFromWorld::ISystemConfigure,
//     gz_2dmap_plugin::OccupancyMapFromWorld::ISystemPostUpdate)

gz::sim::GZ_ADD_PLUGIN(
  gz_2dmap_plugin::OccupancyMapFromWorld,
  gz::sim::System,
  gz::sim::ISystemConfigure,
  gz::sim::ISystemPostUpdate
)

// IGNITION_ADD_PLUGIN_ALIAS(
//     gz_2dmap_plugin::OccupancyMapFromWorld,
//     "ignition::gazebo::systems::OccupancyMapFromWorld")