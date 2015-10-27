FROM mrt_base:latest

#add ros repository
RUN sudo apt-key adv --keyserver pool.sks-keyservers.net --recv-key 0xB01FA116
RUN sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'

#install ros base
RUN sudo apt-get update && sudo apt-get install ros-jade-desktop-full python-rosinstall python-catkin-tools python-rosdep python-rosinstall-generator --yes
RUN sudo rosdep init

