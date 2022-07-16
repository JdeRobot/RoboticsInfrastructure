set(MODEL_NAME vehicle_gate)
set (files 
  model.config
  model.sdf
)

add_subdirectory(meshes)

install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/${MODEL_NAME}/)
