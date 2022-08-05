set(MODEL_NAME cutout_wall)
set (files 
  model.sdf
  model.config
)

add_subdirectory(materials)

install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/${MODEL_NAME}/)
