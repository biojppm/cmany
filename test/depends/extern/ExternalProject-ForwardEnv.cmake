# (C) 2017 Joao Paulo Magalhaes <dev@jpmag.me>

#------------------------------------------------------------------------------
# Get the current cmake environment in a sequence of -DVAR=${VAR}
# declarations so that the environment can be forwarded to an external
# cmake project through CMAKE_ARGS.
#
# Example:
#   ExternalProject_GetFwdArgs(FWD_ARGS)
#   ExternalProject_Add(foo SOURCE_DIR ../foo
#       CMAKE_ARGS ${FWD_ARGS} ... more args)
#
# Use this function to enable forwarding the current cmake environment
# to an external project. It outputs all the needed variables in the
# form of a sequence of -DVAR=value, suitable for use in the CMAKE_ARGS
# clause of ExternalProject_Add().
#
# This function uses ExternalProject_GetFwdVarNames() to find out the
# list of variables to export. If this behaviour does not fit your
# needs, you can append more of your own variables (using the VARS
# argument). The vars specified in this option will each be added to
# the output in the form of -Dvar=${var}. You can also avoid any
# defaults obtained through usage of ExternalProject_GetFwdNames() by
# specifying NO_DEFAULTS.
#
# Example with custom variable names (adding more):
#   ExternalProject_GetFwdVarNames(FWD_ARGS VARS USER_VAR1 USER_VAR2)
#   ExternalProjectAdd(foo SOURCE_DIR ../foo CMAKE_ARGS ${FWD_ARGS})
#
# Example with custom variable names (just your own):
#   ExternalProject_GetFwdVarNames(FWD_ARGS NO_DEFAULTS VARS USER_VAR1 USER_VAR2)
#   ExternalProjectAdd(foo SOURCE_DIR ../foo CMAKE_ARGS ${FWD_ARGS})

function(ExternalProject_GetFwdArgs output_var)
    set(options0arg
        NO_DEFAULTS
        )
    set(options1arg
        )
    set(optionsnarg
        VARS
        )
    cmake_parse_arguments(_epgfa "${options0arg}" "${options1arg}" "${optionsnarg}" ${ARGN})
    if(NOT _epfga_NO_DEFAULTS)
        ExternalProject_GetFwdVarNames(_fwd_names)
    endif()
    list(APPEND ${_epfga_VARS})
    set(_epgfa_args)
    foreach(_f ${_fwd_names})
        if(${_f})
            list(APPEND _epgfa_args -D${_f}=${${_f}})
            message(STATUS "ExternalProject_GetFwdArgs: ${_f}=${${_f}}")
        endif()
    endforeach()

    set(${output_var} "${_epgfa_args}" PARENT_SCOPE)

endfunction(ExternalProject_GetFwdArgs)


#------------------------------------------------------------------------------
# Gets a default list with the names of variables to forward to an
# external project. This function creates a list of common cmake
# variable names which have an impact in the output binaries or their
# placement.
function(ExternalProject_GetFwdVarNames output_var)
    # these common names are irrespective of build type
    set(names
        CMAKE_GENERATOR
        CMAKE_INSTALL_PREFIX
        CMAKE_ARCHIVE_OUTPUT_DIRECTORY
        CMAKE_LIBRARY_OUTPUT_DIRECTORY
        CMAKE_RUNTIME_OUTPUT_DIRECTORY
        CMAKE_AR
        CMAKE_BUILD_TYPE
        CMAKE_INCLUDE_PATH
        CMAKE_LIBRARY_PATH
        #CMAKE_MODULE_PATH # this is dangerous as it can override the external project's build files.
        CMAKE_PREFIX_PATH
        BUILD_SHARED_LIBS
        CMAKE_CXX_COMPILER
        CMAKE_C_COMPILER
        CMAKE_LINKER
        CMAKE_MAKE_PROGRAM
        CMAKE_NM
        CMAKE_OBJCOPY
        CMAKE_RANLIB
        CMAKE_STRIP
        CMAKE_CONFIGURATION_TYPES
        )
    # these names have per-build type values;
    # use CMAKE_CONFIGURATION_TYPES to construct the list
    foreach(v
            CMAKE_CXX_FLAGS
            CMAKE_C_FLAGS
            CMAKE_EXE_LINKER_FLAGS
            CMAKE_MODULE_LINKER_FLAGS
            CMAKE_SHARED_LINKER_FLAGS)
        list(APPEND names ${v})
        foreach(t ${CMAKE_CONFIGURATION_TYPES})
            string(TOUPPER ${t} u)
            list(APPEND names ${v}_${u})
        endforeach()
    endforeach()
    set(${output_var} "${names}" PARENT_SCOPE)
endfunction(ExternalProject_GetFwdVarNames)
