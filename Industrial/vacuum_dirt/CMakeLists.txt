cmake_minimum_required(VERSION 3.8)
project(vacuum_dirt)

# ============================
# C++ standard
# ============================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================
# Warnings
# ============================
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ============================
# Dependencies
# ============================
find_package(ament_cmake REQUIRED)

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED)

# ============================
# Plugin
# ============================
foreach(plugin vacuum_dirt cat_walker)
  add_library(${plugin} SHARED src/${plugin}.cpp)
  target_link_libraries(${plugin}
    gz-sim8::gz-sim8
    gz-plugin2::gz-plugin2
  )
endforeach()

# ============================
# Install
# ============================
install(TARGETS vacuum_dirt cat_walker
  LIBRARY DESTINATION lib
)

install(
  FILES env-hooks/vacuum_dirt.dsv
  DESTINATION share/${PROJECT_NAME}/environment
)

# ============================
# Export
# ============================
ament_export_libraries(vacuum_dirt cat_walker)
ament_export_dependencies(gz-sim8 gz-plugin2)

ament_package()
