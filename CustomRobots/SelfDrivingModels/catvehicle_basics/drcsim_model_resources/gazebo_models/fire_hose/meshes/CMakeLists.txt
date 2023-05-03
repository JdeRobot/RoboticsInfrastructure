set (files 
  coupling.dae
  coupling2.dae
  nozzle.dae
  nozzle2.dae
  coupling.stl
  coupling2.stl
  nozzle.stl
  nozzle2.stl
)
install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/${MODEL_NAME}/meshes/)
