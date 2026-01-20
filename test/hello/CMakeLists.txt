cmake_minimum_required(VERSION 2.12)
project(hello)

add_executable(hello main.cpp)
install(TARGETS hello RUNTIME DESTINATION bin)

