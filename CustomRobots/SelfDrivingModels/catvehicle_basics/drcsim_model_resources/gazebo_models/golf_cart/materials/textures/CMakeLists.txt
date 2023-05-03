set (files 
  texture0.png
  texture1.png
  texture2.png
  texture3.png
  texture4.png
)
install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/${MODEL_NAME}/materials/textures/)
add_subdirectory(no_wheels)
