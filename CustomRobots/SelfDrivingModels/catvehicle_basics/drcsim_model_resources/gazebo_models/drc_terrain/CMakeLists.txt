set(MODEL_NAME drc_terrain)
add_subdirectory(materials)
set (files 
  model.sdf
  model.config
)
install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/${MODEL_NAME}/)
