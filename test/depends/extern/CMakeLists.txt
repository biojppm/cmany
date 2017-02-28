cmake_minimum_required(VERSION 3.2)

project(depends-extern)
include(ExternalProject)
include(ExternalProject-ForwardEnv.cmake)

ExternalProject_GetFwdArgs(FWD_ARGS)

ExternalProject_Add(googletest
    PREFIX googletest
    GIT_REPOSITORY https://github.com/google/googletest
    GIT_TAG release-1.8.0
    CMAKE_GENERATOR "${CMAKE_GENERATOR}"
    CMAKE_ARGS ${FWD_ARGS}
    BINARY_DIR "${CMAKE_BINARY_DIR}/googletest"
    INSTALL_DIR ${CMAKE_INSTALL_PREFIX} # this doesn't work when CMAKE_ARGS is given
    )
