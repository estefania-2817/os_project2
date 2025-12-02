cmake_minimum_required(VERSION 3.10)

project(pp2)

# Include the current directory for header files 

set(CMAKE_C_STANDARD 11)

add_executable(${CMAKE_PROJECT_NAME}
   src/main.c)

target_link_libraries(${CMAKE_PROJECT_NAME} m)