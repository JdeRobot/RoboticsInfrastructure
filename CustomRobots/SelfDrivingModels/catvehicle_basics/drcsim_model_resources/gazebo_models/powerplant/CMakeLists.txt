set(MODEL_NAME powerplant)
add_subdirectory(meshes)
add_subdirectory(materials)
set (files 
  model.sdf
  model.config
)
install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/${MODEL_NAME}/)
