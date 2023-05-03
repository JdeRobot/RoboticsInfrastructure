set (worlds
     atlas.world
     atlas_cpu_lidar.world
     atlas_drc_vehicle_fire_hose.world
     atlas_golf_cart_fire_hose.world

     drc_practice_task_1.world
     drc_practice_task_2.world
     drc_practice_task_3.world
     drc_practice_task_4.world
     drc_practice_task_5.world
     drc_practice_task_6.world
     drc_practice_task_7.world
     drc_practice_task_8.world

     drc_vehicle.world
     golf_cart.world
     powerplant.world
     qual_task_1.world
     qual_task_1_stumps.world
     qual_task_2.world
     qual_task_3.world
     qual_task_3_stumps.world
     qual_task_4.world

     vrc_final_task1.world
     vrc_final_task2.world
     vrc_final_task3.world
     vrc_final_task4.world
     vrc_final_task5.world
     vrc_final_task6.world
     vrc_final_task7.world
     vrc_final_task8.world
     vrc_final_task9.world
     vrc_final_task10.world
     vrc_final_task11.world
     vrc_final_task12.world
     vrc_final_task13.world
     vrc_final_task14.world
     vrc_final_task15.world

     vrc_fire_hose.world
     vrc_task_1.world
     vrc_task_1_cpu_lidar.world
     vrc_task_1_vehicle_start.world
     vrc_task_2.world
     vrc_task_2_cpu_lidar.world
     vrc_task_2_mud_start.world
     vrc_task_2_rubble_start.world
     vrc_task_2_stumps.world
     vrc_task_2_uneven_start.world
     vrc_task_3.world
     vrc_task_3_cpu_lidar.world
     vrc_task_3_firehose_start.world
)

install(FILES ${worlds} DESTINATION ${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}/worlds/)
