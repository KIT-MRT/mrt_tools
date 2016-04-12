FROM mrt_base:latest

#add ros repository
RUN apt-key adv --keyserver pool.sks-keyservers.net --recv-key 0xB01FA116
RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'

#install ros base
ENV ROS_DISTRO jade
RUN apt-get update && apt-get install ros-jade-desktop-full python-rosinstall python-catkin-tools python-rosdep python-rosinstall-generator --yes

# bootstrap rosdep
RUN rosdep init

# setup entrypoint
COPY ./ros_entrypoint.sh /
RUN chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
