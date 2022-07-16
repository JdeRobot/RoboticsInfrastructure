add_subdirectory(block_angle_steps)
add_subdirectory(block_level_steps)
add_subdirectory(block_angle_base)
add_subdirectory(cutout_wall)
add_subdirectory(drc_terrain)
add_subdirectory(drc_vehicle)
add_subdirectory(drc_vehicle_xp900)
add_subdirectory(fire_hose)
add_subdirectory(gate)
add_subdirectory(gate_number_1)
add_subdirectory(gate_number_2)
add_subdirectory(gate_number_3)
add_subdirectory(gate_number_4)
add_subdirectory(gate_number_5)
add_subdirectory(golf_cart)
add_subdirectory(grass_plane)
add_subdirectory(ladder)
add_subdirectory(mud_atlas)
add_subdirectory(mud_atlas_2)
add_subdirectory(pavement_plane)
add_subdirectory(platform_1)
add_subdirectory(platform_2)
add_subdirectory(platform_3)
add_subdirectory(platform_4)
add_subdirectory(powerplant)
add_subdirectory(stepping_block)
add_subdirectory(vehicle_gate)
add_subdirectory(vrc_firehose_long)
add_subdirectory(vrc_firehose_long_a)
add_subdirectory(vrc_firehose_long_b)
add_subdirectory(vrc_firehose_long_c)
add_subdirectory(vrc_grass_plane2)
add_subdirectory(vrc_heightmap_1)
add_subdirectory(vrc_heightmap_2)
add_subdirectory(vrc_heightmap_3)
add_subdirectory(vrc_heightmap_4)
add_subdirectory(vrc_standpipe)
add_subdirectory(vrc_standpipe_a)
add_subdirectory(vrc_standpipe_b)
add_subdirectory(vrc_table)
add_subdirectory(vrc_valve)
add_subdirectory(vrc_valve_a)
add_subdirectory(vrc_valve_b)


set (files
  database.config
)

install(FILES ${files} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/)

# Create symlinks to our sibling ROS packages that are also Gazebo models, so
# that they can be found by Gazebo in our gazebo_models/environments directory
# along with the other models.  This is a workaround for Gazebo #905; once
# GAZEBO_MODEL_PATH can contain elements that are themselves models (as opposed
# to parents of models), these symlink can be removed and our cmake/setup.sh.in
# can be modified to point GAZEBO_MODEL_PATH at the installed locations for
# these sibling packages.
#
# john:
# by not renaming model name when installing standalone models in:
#   atlas_description/CMakeLists.txt  "make_standalone_models(...)"
#   robotiq_hand_description/CMakeLists.txt  "make_standalone_models(...)"
# we don't have to do below
#
# set(package_models
#     atlas_description
#     irobot_hand_description
#     robotiq_hand_description
#     multisense_sl_description)
# if(UNIX)
#   foreach(pm ${package_models})
#     install(CODE "execute_process(
#       COMMAND ${CMAKE_COMMAND} -E create_symlink ../../../${pm} ${pm}
#       WORKING_DIRECTORY ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/gazebo_models/environments/)")
#   endforeach()
# endif(UNIX)
