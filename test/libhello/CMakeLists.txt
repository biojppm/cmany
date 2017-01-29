cmake_minimum_required(VERSION 2.8)
project(libhello)

add_library(hello SHARED hello.hpp hello.cpp)
add_library(hello_static STATIC hello.hpp hello.cpp)

target_compile_definitions(hello PRIVATE HELLO_EXPORT)
set_target_properties(hello_static PROPERTIES OUTPUT_NAME hello)

set_target_properties(hello_static hello PROPERTIES
    PUBLIC_HEADER hello.hpp)
target_include_directories(hello
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include/hello>)
target_include_directories(hello_static
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include/hello>)

install(FILES hello.hpp DESTINATION include/hello)
install(TARGETS hello hello_static
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib/static
        PUBLIC_HEADER DESTINATION include/hello)


add_executable(test_hello main.cpp)
target_link_libraries(test_hello hello)

add_executable(test_hello_static main.cpp)
target_link_libraries(test_hello_static hello_static)
