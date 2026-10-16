find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)

# Workers that carry boxes around the warehouse delivery world
add_library(warehouse_workers SHARED src/warehouse_workers.cpp)
target_compile_features(warehouse_workers PRIVATE cxx_std_17)
target_link_libraries(warehouse_workers
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2)

install(
  TARGETS warehouse_workers
  LIBRARY DESTINATION lib)
