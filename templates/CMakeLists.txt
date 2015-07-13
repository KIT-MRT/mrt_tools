cmake_minimum_required(VERSION 2.8.3)
project(${CMAKE_PACKAGE_NAME})

###################
## find packages ##
###################
include(UseMrtModules)
include(UseMrtStdCompilerFlags)

include(GatherDeps)
#remove libs, which cannot be find automatically
#list(REMOVE_ITEM DEPENDEND_PACKAGES <package name 1> <package name 2> ...)
find_package(DependendPackages REQUIRED COMPONENTS ${DEPENDEND_PACKAGES})

#manually resolve removed dependend packages
#find_package(...)

@ xxxx@ ################################################
@ xxxx@ ## Declare ROS messages, services and actions ##
@ xxxx@ ################################################
@ xxxx@ 
@ xxxx@ ## To declare and build messages, services or actions from within this
@ xxxx@ ## package, follow these steps:
@ xxxx@ ## * Let MSG_DEP_SET be the set of packages whose message types you use in
@ xxxx@ ##   your messages/services/actions (e.g. std_msgs, actionlib_msgs, ...).
@ xxxx@ ## * In the file package.xml:
@ xxxx@ ##   * add a build_depend and a run_depend tag for each package in MSG_DEP_SET
@ xxxx@ ##   * If MSG_DEP_SET isn't empty the following dependencies might have been
@ xxxx@ ##     pulled in transitively but can be declared for certainty nonetheless:
@ xxxx@ ##     * add a build_depend tag for "message_generation"
@ xxxx@ ##     * add a run_depend tag for "message_runtime"
@ xxxx@ ## * In this file (CMakeLists.txt):
@ xxxx@ ##   * add "message_generation" and every package in MSG_DEP_SET to
@ xxxx@ ##     find_package(catkin REQUIRED COMPONENTS ...)
@ xxxx@ ##   * add "message_runtime" and every package in MSG_DEP_SET to
@ xxxx@ ##     catkin_package(CATKIN_DEPENDS ...)
@ xxxx@ ##   * uncomment the add_*_files sections below as needed
@ xxxx@ ##     and list every .msg/.srv/.action file to be processed
@ xxxx@ ##   * uncomment the generate_messages entry below
@ xxxx@ ##   * add every package in MSG_DEP_SET to generate_messages(DEPENDENCIES ...)
@ xxxx@ 
@ xxxx@ ## Generate messages in the 'msg' folder
@ xxxx@ # file(GLOB_RECURSE ROS_MESSAGE_FILES RELATIVE "msg/*.msg")
@ xxxx@ # add_message_files(
@ xxxx@ #   FILES
@ xxxx@ #   ${ROS_MESSAGE_FILES}
@ xxxx@ # )
@ xxxx@ 
@ xxxx@ ## Generate services in the 'srv' folder
@ xxxx@ # file(GLOB_RECURSE ROS_SERVICE_FILES RELATIVE "srv/*.srv")
@ xxxx@ # add_service_files(
@ xxxx@ #   FILES
@ xxxx@ #   ${ROS_SERVICE_FILES}
@ xxxx@ # )
@ xxxx@ 
@ xxxx@ ## Generate actions in the 'action' folder
@ xxxx@ # file(GLOB_RECURSE ROS_ACTION_FILES RELATIVE "action/*.action")
@ xxxx@ # add_action_files(
@ xxxx@ #   FILES
@ xxxx@ #   ${ROS_ACTION_FILES}
@ xxxx@ # )
@ xxxx@ 
@ xxxx@ ## Generate added messages and services with any dependencies listed here
@ xxxx@ # generate_messages(
@ xxxx@ #   DEPENDENCIES
@ xxxx@ #   std_msgs  # Or other packages containing msgs
@ xxxx@ # )
@ xxxx@ 
###################################
## catkin specific configuration ##
###################################
## The catkin_package macro generates cmake config files for your package
## Declare things to be passed to dependent projects
## INCLUDE_DIRS: uncomment this if you package contains header files
## LIBRARIES: libraries you create in this project that dependent projects also need
## CATKIN_DEPENDS: catkin_packages dependent projects also need
## DEPENDS: system dependencies of this project that dependent projects also need
catkin_package(
  INCLUDE_DIRS include ${mrt_EXPORT_INCLUDE_DIRS}
  LIBRARIES ${PROJECT_NAME} ${mrt_EXPORT_LIBRARIES}
  CATKIN_DEPENDS ${catkin_EXPORT_DEPENDS}
)

@xx xx@ ###########
@xx xx@ ## Build ##
@xx xx@ ###########
@xx xx@ # Add include and library directories
@xx xx@ include_directories(
@xx xx@   include
@xx xx@   ${mrt_INCLUDE_DIRS} 
@xx xx@   ${catkin_INCLUDE_DIRS}
@xx xx@ )
@xx xx@ 
@xx xx@ link_directories(
@xx xx@   ${mrt_LIBRARY_DIRS}
@xx xx@ )
@xx xx@ 
@xx xx@ file(GLOB_RECURSE PROJECT_HEADER_FILES_INC RELATIVE "include/*.h")
@xx xx@ file(GLOB_RECURSE PROJECT_SOURCE_FILES_INC RELATIVE "src/*.h")
@xx xx@ file(GLOB_RECURSE PROJECT_SOURCE_FILES_SRC RELATIVE "src/*.cpp")
@xx xx@ 
@xx  x@ # Declare a cpp executable
@xx  x@ add_executable(${PROJECT_NAME}
@xx  x@   ${PROJECT_HEADER_FILES_INC}
@xx  x@   ${PROJECT_SOURCE_FILES_INC}
@xx  x@   ${PROJECT_SOURCE_FILES_SRC}
@xx  x@ )
@xx  x@ 
@xx x @ # Declare a cpp library
@xx x @ add_library(${PROJECT_NAME}
@xx x @   ${PROJECT_HEADER_FILES_INC}
@xx x @   ${PROJECT_SOURCE_FILES_INC}
@xx x @   ${PROJECT_SOURCE_FILES_SRC}
@xx x @ )
@xx x @ 
@ x xx@ # Add cmake target dependencies of the executable/library
@ x xx@ # as an example, message headers may need to be generated before nodes
@ x xx@ add_dependencies(${PROJECT_NAME} ${catkin_EXPORTED_TARGETS})
@ x xx@ 
@xx xx@ # Specify libraries to link a library or executable target against
@xx xx@ target_link_libraries(${PROJECT_NAME}
@xx xx@   ${catkin_LIBRARIES}
@xx xx@   ${mrt_LIBRARIES}
@xx xx@ )
@xx xx@ 
#############
## Install ##
#############
@xx xx@ # Mark executables and/or libraries for installation
@xx xx@ install(TARGETS ${PROJECT_NAME}
@xx xx@   ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
@xx xx@   LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
@xx xx@   RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
@xx xx@ )
@xx xx@ 
@xx xx@ # Mark cpp header files for installation
@xx xx@ install(DIRECTORY include/${PROJECT_NAME}/
@xx xx@   DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
@xx xx@   FILES_MATCHING PATTERN "*.h"
@xx xx@ )
@xx xx@ 
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
  target_link_libraries(${PROJECT_NAME}-test ${PROJECT_NAME})
endif()

