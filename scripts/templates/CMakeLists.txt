@  |  @ #This file contains the different versions for which file stuff is used
@  |  @ #for ros, non-ros and header only library, library or executable
@  |  @ #
@  |  @ #The mask is as follows
@  |  @ #@12|345@
@  |  @ #pos1: non ros package
@  |  @ #pos2: ros package
@  |  @ #pos3: library
@  |  @ #pos4: executable
@  |  @ #
@  |  @ #Put a "x" at the position to enable this line
@  |  @ #E.g a non-ros library has the following mask: @x |x @
#pkg_version=1.3
cmake_minimum_required(VERSION 2.8.3)
project(${CMAKE_PACKAGE_NAME})

###################
## find packages ##
###################
include(UseMrtModules)
include(UseMrtStdCompilerFlags)
include(UseMrtAutoTarget)

include(GatherDeps)
#remove libs, which cannot be find automatically
#list(REMOVE_ITEM DEPENDEND_PACKAGES <package name 1> <package name 2> ...)
find_package(AutoDeps REQUIRED COMPONENTS ${DEPENDEND_PACKAGES})

#manually resolve removed dependend packages
#find_package(...)

@ x|xx@ ################################################
@ x|xx@ ## Declare ROS messages, services and actions ##
@ x|xx@ ################################################
@ x|xx@ 
@ x|xx@ # To declare and build messages, services or actions from within this
@ x|xx@ # package, follow these steps:
@ x|xx@ # * Let MSG_DEP_SET be the set of packages whose message types you use in
@ x|xx@ #   your messages/services/actions (e.g. std_msgs, actionlib_msgs, ...).
@ x|xx@ # * In the file package.xml:
@ x|xx@ #   * add a build_depend and a run_depend tag for each package in MSG_DEP_SET
@ x|xx@ #   * If MSG_DEP_SET isn't empty the following dependencies might have been
@ x|xx@ #     pulled in transitively but can be declared for certainty nonetheless:
@ x|xx@ #     * add a build_depend tag for "message_generation"
@ x|xx@ #     * add a run_depend tag for "message_runtime"
@ x|xx@ # * In this file (CMakeLists.txt):
@ x|xx@ #   * add "message_generation" and every package in MSG_DEP_SET to
@ x|xx@ #     find_package(catkin REQUIRED COMPONENTS ...)
@ x|xx@ #   * add "message_runtime" and every package in MSG_DEP_SET to
@ x|xx@ #     catkin_package(CATKIN_DEPENDS ...)
@ x|xx@ #   * uncomment the add_*_files sections below as needed
@ x|xx@ #     and list every .msg/.srv/.action file to be processed
@ x|xx@ #   * uncomment the generate_messages entry below
@ x|xx@ #   * add every package in MSG_DEP_SET to generate_messages(DEPENDENCIES ...)
@ x|xx@ 
@ x|xx@ # Generate messages in the 'msg' folder
@ x|xx@ file(GLOB ROS_MESSAGE_FILES RELATIVE "${CMAKE_CURRENT_LIST_DIR}/msg" "msg/*.msg")
@ x|xx@ if (ROS_MESSAGE_FILES)
@ x|xx@ 	add_message_files(
@ x|xx@ 	  FILES
@ x|xx@ 	  ${ROS_MESSAGE_FILES}
@ x|xx@ 	)
@ x|xx@ 	set(ROS_GENERATE_MESSAGES True)
@ x|xx@ endif()
@ x|xx@ 
@ x|xx@ # Generate services in the 'srv' folder
@ x|xx@ file(GLOB ROS_SERVICE_FILES RELATIVE "${CMAKE_CURRENT_LIST_DIR}/srv" "srv/*.srv")
@ x|xx@ if (ROS_SERVICE_FILES)
@ x|xx@ 	add_service_files(
@ x|xx@ 	  FILES
@ x|xx@ 	  ${ROS_SERVICE_FILES}
@ x|xx@ 	)
@ x|xx@ 	set(ROS_GENERATE_MESSAGES True)
@ x|xx@ endif()
@ x|xx@ 
@ x|xx@ # Generate actions in the 'action' folder
@ x|xx@ file(GLOB ROS_ACTION_FILES RELATIVE "${CMAKE_CURRENT_LIST_DIR}/action" "action/*.action")
@ x|xx@ if (ROS_ACTION_FILES)
@ x|xx@ 	add_action_files(
@ x|xx@ 	  FILES
@ x|xx@ 	  ${ROS_ACTION_FILES}
@ x|xx@ 	)
@ x|xx@ 	set(ROS_GENERATE_MESSAGES True)
@ x|xx@ endif()
@ x|xx@ 
@ x|xx@ # Generate added messages and services with any dependencies listed here
@ x|xx@ if (ROS_GENERATE_MESSAGES)
@ x|xx@ 	generate_messages(
@ x|xx@ 	  DEPENDENCIES
@ x|xx@ 	  #add dependencies here
@ x|xx@ 	)
@ x|xx@ endif()
@ x|xx@ 
@xx|x @ ############################
@xx|x @ ## read source code files ##
@xx|x @ ############################
@xx|x @ file(GLOB PROJECT_HEADER_FILES_INC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "include/*.h")
@xx|x @ file(GLOB PROJECT_SOURCE_FILES_INC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "src/*.h")
@xx|x @ file(GLOB PROJECT_SOURCE_FILES_SRC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "src/*.cpp")
@xx|x @ 
@xx|x @ if (PROJECT_SOURCE_FILES_SRC)
@xx|x @ 	set(LIBRARY_NAME ${PROJECT_NAME})
@xx|x @ endif()
@xx|x @ 
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
@xx|x @   INCLUDE_DIRS include ${mrt_EXPORT_INCLUDE_DIRS}
@xx|x @   LIBRARIES ${LIBRARY_NAME} ${mrt_EXPORT_LIBRARIES}
@xx|x @   CATKIN_DEPENDS ${catkin_EXPORT_DEPENDS}
)

@xx|xx@ ###########
@xx|xx@ ## Build ##
@xx|xx@ ###########
@xx|xx@ # Add include and library directories
@xx|xx@ include_directories(
@xx|x @   include/${LIBRARY_NAME}
@xx|xx@   ${mrt_INCLUDE_DIRS} 
@xx|xx@   ${catkin_INCLUDE_DIRS}
@xx|xx@ )
@xx|xx@ 
@xx|xx@ link_directories(
@xx|xx@   ${mrt_LIBRARY_DIRS}
@xx|xx@ )
@xx|xx@ 
@xx|x @ if (PROJECT_SOURCE_FILES_SRC)
@xx|x @ 	# Declare a cpp library
@xx|x @ 	add_library(${LIBRARY_NAME}
@xx|x @ 	  ${PROJECT_HEADER_FILES_INC}
@xx|x @ 	  ${PROJECT_SOURCE_FILES_INC}
@xx|x @ 	  ${PROJECT_SOURCE_FILES_SRC}
@xx|x @ 	)
@xx|x @ 	
@ x|x @ 	# Add cmake target dependencies of the executable/library
@ x|x @ 	# as an example, message headers may need to be generated before nodes
@ x|x @ 	add_dependencies(${PROJECT_NAME} ${catkin_EXPORTED_TARGETS})
@ x|x @ 	
@xx|x @ 	# Specify libraries to link a library or executable target against
@xx|x @ 	target_link_libraries(${PROJECT_NAME}
@xx|x @ 	  ${catkin_LIBRARIES}
@xx|x @ 	  ${mrt_LIBRARIES}
@xx|x @ 	)
@xx|x @ endif()
@xx|x @ 
@xx| x@ function(add_exec EXEC_NAME SEARCH_FOLDER)
@xx| x@ 	#glob all files in this directory
@xx| x@ 	file(GLOB EXEC_SOURCE_FILES_INC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "${SEARCH_FOLDER}/*.h")
@xx| x@ 	file(GLOB EXEC_SOURCE_FILES_SRC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "${SEARCH_FOLDER}/*.cpp")
@xx| x@ 
@xx| x@ 	if (PROJECT_SOURCE_FILES_SRC)
@xx| x@ 		#add executable
@xx| x@ 		add_executable(${EXEC_NAME}
@xx| x@ 			${EXEC_SOURCE_FILES_INC}
@xx| x@ 			${EXEC_SOURCE_FILES_SRC}
@xx| x@ 		)
@xx| x@ 
@ x| x@ 		# Add cmake target dependencies of the executable/library
@ x| x@ 		# as an example, message headers may need to be generated before nodes
@ x| x@ 		add_dependencies(${EXEC_NAME} ${catkin_EXPORTED_TARGETS})
@ x| x@ 		if (${EXEC_NAME}_EXPORTED_TARGETS)
@ x| x@ 		    add_dependencies(${EXEC_NAME} ${${EXEC_NAME}_EXPORTED_TARGETS})
@ x| x@ 		endif (${EXEC_NAME}_EXPORTED_TARGETS)
@ x| x@ 	
@xx| x@ 		# Specify libraries to link a library or executable target against
@xx| x@ 		target_link_libraries(${EXEC_NAME}
@xx| x@ 		  ${catkin_LIBRARIES}
@xx| x@ 		  ${mrt_LIBRARIES}
@xx| x@ 		)
@xx| x@ 
@xx| x@ 		# Mark executables and/or libraries for installation
@xx| x@ 		install(TARGETS ${EXEC_NAME}
@xx| x@ 		  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
@xx| x@ 		  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
@xx| x@ 		  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
@xx| x@ 		)
@xx| x@ 	endif()
@xx| x@ endfunction()
@xx| x@ 
@xx| x@ glob_folders(SRC_DIRECTORIES "${CMAKE_CURRENT_SOURCE_DIR}/src")
@xx| x@ 
@xx| x@ if (SRC_DIRECTORIES)
@xx| x@ 	#found subfolders, add executable for each subfolder
@xx| x@ 	foreach(SRC_DIR ${SRC_DIRECTORIES})
@xx| x@ 		add_exec(${SRC_DIR} "src/${SRC_DIR}")
@xx| x@ 	endforeach()
@xx| x@ else()
@xx| x@ 	#no subfolder found, add executable for src folder
@xx| x@ 	add_exec(${PROJECT_NAME} "src")
@xx| x@ endif()
@xx| x@ 

#############
## Install ##
#############
@xx|x @ if (TARGET ${PROJECT_NAME})
@xx|x @ 	# Mark library for installation
@xx|x @ 	install(TARGETS ${PROJECT_NAME}
@xx|x @ 	  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
@xx|x @ 	  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
@xx|x @ 	  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
@xx|x @ 	)
@xx|x @ endif()
@xx|x @ 
@xx|x @ # Mark c++ header files for installation
@xx|x @ install(DIRECTORY include/${PROJECT_NAME}/
@xx|x @   DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
@xx|x @   FILES_MATCHING PATTERN "*.h"
@xx|x @ )
@xx|x @ 
#install(FILES
#  res/test.png
#  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
#)

#############
## Testing ##
#############
# Add gtest based cpp test target and link libraries
if (CATKIN_ENABLE_TESTING)
	file(GLOB PROJECT_TEST_FILES_SRC RELATIVE "${CMAKE_CURRENT_LIST_DIR}" "test/*.cpp")
	foreach(PROJECT_TEST_FILE_SRC ${PROJECT_TEST_FILES_SRC})
		get_filename_component(PROJECT_TEST_NAME ${PROJECT_TEST_FILE_SRC} NAME_WE)
		
		catkin_add_gtest(${PROJECT_TEST_NAME}-test ${PROJECT_TEST_FILES_SRC})
@xx|x @ 		target_link_libraries(${PROJECT_TEST_NAME}-test ${LIBRARY_NAME} ${catkin_LIBRARIES} ${mrt_LIBRARIES})
@xx| x@ 		target_link_libraries(${PROJECT_TEST_NAME}-test ${catkin_LIBRARIES} ${mrt_LIBRARIES})
	endforeach()
endif()