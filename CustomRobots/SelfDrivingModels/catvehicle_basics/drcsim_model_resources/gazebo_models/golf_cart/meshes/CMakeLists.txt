set (files 
  model.dae
  no_wheels.dae
  no_wheels.stl
  no_wheels_test.dae
)
install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/${MODEL_NAME}/meshes/)
