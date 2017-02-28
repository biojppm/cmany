cmake_minimum_required(VERSION 3.2)

project(depends)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../libhello libhello)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../libhello)

find_library(LIBGTEST gtest REQUIRED)
find_library(LIBGTEST_MAIN gtest_main REQUIRED)
find_path(GTEST_INC gtest/gtest.h REQUIRED)
include_directories(${GTEST_INC})

message(STATUS "LIBGTEST=${LIBGTEST}")
message(STATUS "LIBGTEST_MAIN=${LIBGTEST_MAIN}")
message(STATUS "GTEST_INC=${GTEST_INC}")

add_executable(gtest_hello_static main.cpp)
target_link_libraries(gtest_hello_static hello_static ${LIBGTEST} ${LIBGTEST_MAIN})

add_executable(gtest_hello main.cpp)
target_link_libraries(gtest_hello hello ${LIBGTEST} ${LIBGTEST_MAIN})
