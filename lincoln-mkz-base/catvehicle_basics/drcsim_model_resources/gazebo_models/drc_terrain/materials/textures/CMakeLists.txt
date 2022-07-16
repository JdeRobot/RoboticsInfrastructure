set (files 
  drc_sim_v0_terrain.png
  drc_sim_v1_terrain.png
)
install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/${MODEL_NAME}/materials/textures/)
