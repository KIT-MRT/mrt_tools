@  |   @ #This file contains the different versions for which file stuff is used
@  |   @ #for ros, non-ros and header only library, library or executable
@  |   @ #
@  |   @ #The mask is as follows
@  |   @ #@12|345@
@  |   @ #pos1: non ros package
@  |   @ #pos2: ros package
@  |   @ #pos3: header only library
@  |   @ #pos4: library
@  |   @ #pos5: executable
@  |   @ #
@  |   @ #Put a "x" at the position to enable this line
@  |   @ #E.g a non-ros library has the following mask: @x | x @
cmake_minimum_required(VERSION 2.8.3)
project(${CMAKE_PACKAGE_NAME})

###################
## find packages ##
###################
include(UseMrtModules)
include(UseMrtStdCompilerFlags)
@xx| xx@ include(UseMrtAutoTarget)

include(GatherDeps)
#remove libs, which cannot be find automatically
#list(REMOVE_ITEM DEPENDEND_PACKAGES <package name 1> <package name 2> ...)
find_package(AutoDeps REQUIRED COMPONENTS ${DEPENDEND_PACKAGES})

#manually resolve removed dependend packages
#find_package(...)

@ x|xxx@ ################################################
@ x|xxx@ ## Declare ROS messages, services and actions ##
@ x|xxx@ ################################################
@ x|xxx@ 
@ x|xxx@ # To declare and build messages, services or actions from within this
@ x|xxx@ # package, follow these steps:
@ x|xxx@ # * Let MSG_DEP_SET be the set of packages whose message types you use in
@ x|xxx@ #   your messages/services/actions (e.g. std_msgs, actionlib_msgs, ...).
@ x|xxx@ # * In the file package.xml:
@ x|xxx@ #   * add a build_depend and a run_depend tag for each package in MSG_DEP_SET
@ x|xxx@ #   * If MSG_DEP_SET isn't empty the following dependencies might have been
@ x|xxx@ #     pulled in transitively but can be declared for certainty nonetheless:
@ x|xxx@ #     * add a build_depend tag for "message_generation"
@ x|xxx@ #     * add a run_depend tag for "message_runtime"
@ x|xxx@ # * In this file (CMakeLists.txt):
@ x|xxx@ #   * add "message_generation" and every package in MSG_DEP_SET to
@ x|xxx@ #     find_package(catkin REQUIRED COMPONENTS ...)
@ x|xxx@ #   * add "message_runtime" and every package in MSG_DEP_SET to
@ x|xxx@ #     catkin_package(CATKIN_DEPENDS ...)
@ x|xxx@ #   * uncomment the add_*_files sections below as needed
@ x|xxx@ #     and list every .msg/.srv/.action file to be processed
@ x|xxx@ #   * uncomment the generate_messages entry below
@ x|xxx@ #   * add every package in MSG_DEP_SET to generate_messages(DEPENDENCIES ...)
@ x|xxx@ 
@ x|xxx@ ## Generate messages in the 'msg' folder
@ x|xxx@ #file(GLOB_RECURSE ROS_MESSAGE_FILES RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "msg/*.msg")
@ x|xxx@ #add_message_files(
@ x|xxx@ #  FILES
@ x|xxx@ #  ${ROS_MESSAGE_FILES}
@ x|xxx@ #)
@ x|xxx@ 
@ x|xxx@ ## Generate services in the 'srv' folder
@ x|xxx@ #file(GLOB_RECURSE ROS_SERVICE_FILES RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "srv/*.srv")
@ x|xxx@ #add_service_files(
@ x|xxx@ #  FILES
@ x|xxx@ #  ${ROS_SERVICE_FILES}
@ x|xxx@ #)
@ x|xxx@ 
@ x|xxx@ ## Generate actions in the 'action' folder
@ x|xxx@ #file(GLOB_RECURSE ROS_ACTION_FILES RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "action/*.action")
@ x|xxx@ #add_action_files(
@ x|xxx@ #  FILES
@ x|xxx@ #  ${ROS_ACTION_FILES}
@ x|xxx@ #)
@ x|xxx@ 
@ x|xxx@ ## Generate added messages and services with any dependencies listed here
@ x|xxx@ #generate_messages(
@ x|xxx@ #  DEPENDENCIES
@ x|xxx@ #  std_msgs  # Or other packages containing msgs
@ x|xxx@ #)
@ x|xxx@ 
###################################
## catkin specific configuration ##
###################################
# The catkin_package macro generates cmake config files for your package
# Declare things to be passed to dependent projects
# INCLUDE_DIRS: uncomment this if you package contains header files
# LIBRARIES: libraries you create in this project that dependent projects also need
# CATKIN_DEPENDS: catkin_packages dependent projects also need
# DEPENDS: system dependencies of this project that dependent projects also need
catkin_package(
  INCLUDE_DIRS include ${mrt_EXPORT_INCLUDE_DIRS}
@xx| xx@   LIBRARIES ${PROJECT_NAME} ${mrt_EXPORT_LIBRARIES}
@xx|x  @   LIBRARIES ${mrt_EXPORT_LIBRARIES}
  CATKIN_DEPENDS ${catkin_EXPORT_DEPENDS}
)

@xx| xx@ ###########
@xx| xx@ ## Build ##
@xx| xx@ ###########
@xx| xx@ # Add include and library directories
@xx| xx@ include_directories(
@xx| xx@   include
@xx| xx@   ${mrt_INCLUDE_DIRS} 
@xx| xx@   ${catkin_INCLUDE_DIRS}
@xx| xx@ )
@xx| xx@ 
@xx| xx@ link_directories(
@xx| xx@   ${mrt_LIBRARY_DIRS}
@xx| xx@ )
@xx| xx@ 
@xx| xx@ file(GLOB_RECURSE PROJECT_HEADER_FILES_INC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "include/*.h")
@xx| xx@ file(GLOB_RECURSE PROJECT_SOURCE_FILES_INC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "src/*.h")
@xx| xx@ file(GLOB_RECURSE PROJECT_SOURCE_FILES_SRC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "src/*.cpp")
@xx| xx@ 
@xx|  x@ # Declare a cpp executable
@xx|  x@ add_executable_auto(${PROJECT_NAME}
@xx|  x@   ${PROJECT_HEADER_FILES_INC}
@xx|  x@   ${PROJECT_SOURCE_FILES_INC}
@xx|  x@   ${PROJECT_SOURCE_FILES_SRC}
@xx|  x@ )
@xx|  x@ 
@xx| x @ # Declare a cpp library
@xx| x @ add_library_auto(${PROJECT_NAME}
@xx| x @   ${PROJECT_HEADER_FILES_INC}
@xx| x @   ${PROJECT_SOURCE_FILES_INC}
@xx| x @   ${PROJECT_SOURCE_FILES_SRC}
@xx| x @ )
@xx| x @ 
@ x| xx@ # Add cmake target dependencies of the executable/library
@ x| xx@ # as an example, message headers may need to be generated before nodes
@ x| xx@ add_dependencies(${PROJECT_NAME} ${catkin_EXPORTED_TARGETS})
@ x| xx@ 
@xx| xx@ # Specify libraries to link a library or executable target against
@xx| xx@ target_link_libraries(${PROJECT_NAME}
@xx| xx@   ${catkin_LIBRARIES}
@xx| xx@   ${mrt_LIBRARIES}
@xx| xx@ )
@xx| xx@ 
#############
## Install ##
#############
@xx| xx@ # Mark executables and/or libraries for installation
@xx| xx@ install(TARGETS ${PROJECT_NAME}
@xx| xx@   ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
@xx| xx@   LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
@xx| xx@   RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
@xx| xx@ )
@xx| xx@ 
@xx| xx@ # Mark cpp header files for installation
@xx| xx@ install(DIRECTORY include/${PROJECT_NAME}/
@xx| xx@   DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
@xx| xx@   FILES_MATCHING PATTERN "*.h"
@xx| xx@ )
@xx| xx@ 
#install(FILES
#  res/test.png
#  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
#)

#############
## Testing ##
#############
# Add gtest based cpp test target and link libraries
catkin_add_gtest(${PROJECT_NAME}-test test/test_${PROJECT_NAME}.cpp)
if(TARGET ${PROJECT_NAME}-test)
@xx| x @   target_link_libraries(${PROJECT_NAME}-test ${PROJECT_NAME})
@xx|x x@   #target_link_libraries(${PROJECT_NAME}-test)
endif()

