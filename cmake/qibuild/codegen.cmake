## Copyright (c) 2012-2019 SoftBank Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.


#! Source code generation
# =======================

#! Generate a source file
#
# Example of use: ::
#
#    set(_input ${CMAKE_CURRENT_SOURCE_DIR}/input.data)
#    set(_output ${CMAKE_CURRENT_BINARY_DIR}/generated.c)
#    qi_generate_src(${_output} SRC ${_input} COMMAND my_script ${_input} -o ${_output})
#    qi_create_bin(my_bin ${_output} main.c)
#
# Note that the base dir of the output will automatically be created, so
# you do not have to worry about it in your script.
#
# Also note that you should consider adding an explicit dependency to the
# command that generates the sources, using the DEPENDS argument:
#
# For instance, when using a Python script::
#
#      qi_generate_src(...
#           COMMAND ${PYTHON2_EXECUTABLE} myscript.py ...
#           DEPENDS myscript.py
#     )
#
# Or when using a target::
#
#      find_package(FOO REQUIRED)
#
#      qi_generate_src(...
#           COMMAND ${FOO_EXECUTABLE} myscript.py ...
#           DEPENDS ${FOO_EXECUTABLE}
#     )
#
# \arg:out the generated files in a list
# \group:SRC a group of sources to take as input
# \group:COMMAND the command to run to generate the files
# \arg:COMMENT a comment to be displayed while generating the source file
function(qi_generate_src)
  cmake_parse_arguments(ARG "" "COMMENT" "SRC;COMMAND;DEPENDS" ${ARGN})
  set(out ${ARG_UNPARSED_ARGUMENTS})
  foreach(_out_file ${out})
    set_source_files_properties(${_out_file}
        PROPERTIES GENERATED TRUE)
    get_filename_component(_out_dir ${_out_file} PATH)
    if(_out_dir)
      file(MAKE_DIRECTORY ${_out_dir})
    endif()
  endforeach()
  set(_comment "Generating ${out} ....")
  if(ARG_COMMENT)
    set(_comment ${ARG_COMMENT})
  endif()
  list(GET ARG_COMMAND 0 _cmd)
  list(REMOVE_AT ARG_COMMAND 0)
  add_custom_command(OUTPUT ${out}
                     COMMENT "${_comment}"
                     COMMAND ${_cmd}
                     ARGS ${ARG_COMMAND}
                     DEPENDS ${ARG_SRC} ${ARG_DEPENDS}
  )
endfunction()


#! Generate a header
#
# Example of use: ::
#
#   set(_input ${CMAKE_CURRENT_SOURCE_DIR}/input.data)
#   set(_generated_h ${CMAKE_CURRENT_BINARY_DIR}/generated.h)
#   qi_generate_header(${_generated_h} SRC ${_input}
#    COMMAND my_script ${_input} -o ${_generated_h})
#   qi_create_bin(foo ${_generated_h} main.c)
#   qi_install_header(${_generated_h})
#
# Notes:
#  * the base dir of the header will automatically be created, so
#    you do not have to worry about it in your script.
#  * ``include_directories()`` will be called with the directory where
#    the header is generated.
#  * As with :cmake:function:`qi_generate_src`, you should specify
#    a ``DEPENDS`` argument.
#
#
# \arg:out the resulting source file
# \group:SRC a group of sources to take as input
# \group:COMMAND the command to run to generate the source file
# \arg:COMMENT a comment to be displayed while generating the source file
function(qi_generate_header out)
  get_filename_component(_header_dir ${out} PATH)
  include_directories(${_header_dir})
  qi_generate_src(${out} ${ARGN})
endfunction()


#! Generate a trampoline script in stage binary dir that bounces to an other script in source dir
#
# To be used if your script needs to run from src dir, and access some built libraries or
# other components.
#
# \arg: out name of the output file, will be put in sdk binary dir.
# \arg: in script source file below src directory
# \group: List of dependencies the script uses.
# \flag:PYTHON set if the script is a python script.
#
# The trampoline scripts sets the following variables:
#  - The appropriate LIBRARY__PATH variable for the platform
#  - PYTHONPATH (Not yet supported)
#  - QI_PATH to all the paths added to the other variables
#
# \warning for maximum portability, always explicitly invoke python when
# running the trampoline script.
function(qi_generate_trampoline out in)
  cmake_parse_arguments(ARG
  "PYTHON"
  ""
  "DEPENDS"
  ${ARGN})
  set(_res
  "# Autogenerated file, do not edit or change location.
# Just sets some variables and bounce to @SCRIPT@
import os
import sys
import subprocess

env = os.environ.copy()
env['@PATHNAME@'] = env.get('@PATHNAME@', '') + '@PATH@'
env['QI_PATH'] = env.get('QI_PATH', '') + '@PATH@'
if '@PYTHONPATH@':
  env['PYTHONPATH'] = env.get('PYTHONPATH', '') + '@PYTHONPATH@'
args = []
if @INTERPRETER@:
  args.append(@INTERPRETER@)
args.append('@SCRIPT@')
args += sys.argv[1:]
rv = subprocess.call(args, env=env)
sys.exit(rv)
")
  if(APPLE)
    set(_os_path_var_name "DYLD_LIBRARY_PATH")
    set(_os_pathsep ":")
  elseif(UNIX)
    set(_os_path_var_name "LD_LIBRARY_PATH")
    set(_os_pathsep ":")
  else()
    set(_os_path_var_name "PATH")
    set(_os_pathsep "\\;")
  endif()
  set(_PATH)
  set(_interpreter)
  if(ARG_PYTHON)
    set(_interpreter "sys.executable")
  endif()
  # FIXME: maybe use CMAKE_FIND_ROOT_PATH: all sdk roots
  # or read sdk/share/qi/path.conf
  # Careful below, ${foo}_LIBRARIES has inconsistent formating.
  # can be shared;foo, path/to/foo, or -lfoo
  _qi_use_lib_get_deps(_deplist ${ARG_DEPENDS})
  foreach(_dep ${_deplist})
    find_package(${_dep})
    set(_lib ${${_dep}_LIBRARIES})
    if(_lib)
      list(LENGTH _lib _len)
      if (_len GREATER 1)
        list(GET _lib 1 _libname)
        get_filename_component(_path "${_libname}" PATH)
        if(WIN32)
          set(_path "${_path}/../bin")
        endif()
        set(_PATH "${_PATH}${_os_pathsep}${_path}")
      endif()
    endif()
  endforeach()
  string(REPLACE "@PATHNAME@" ${_os_path_var_name} _rep "${_res}")
  set(_res "${_rep}")
  string(REPLACE "@SCRIPT@" "${CMAKE_CURRENT_SOURCE_DIR}/${in}" _rep "${_res}")
  set(_res "${_rep}")
  string(REPLACE "@PATH@" "${_PATH}" _rep "${_res}")
  set(_res "${_rep}")
  string(REPLACE "@PYTHONPATH@" "" _rep "${_res}")
  set(_res "${_rep}")
  string(REPLACE "@INTERPRETER@" "${_interpreter}" _rep "${_res}")
  set(_res "${_rep}")
  file(WRITE  "${QI_SDK_DIR}/${QI_SDK_BIN}/${out}" "${_res}")
endfunction()
