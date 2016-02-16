FROM mrt_ros_desktop_full:latest

#add apt-chacher
RUN echo "Acquire::http::Proxy \"http://mrtknecht:3142\";" | sudo tee "/etc/apt/apt.conf.d/01proxy" > /dev/null

#add mrt repository
RUN sudo apt-key adv --keyserver pool.sks-keyservers.net --recv-key 0x66FF02D7
RUN echo "deb [arch=amd64] http://mrtdeb/deb trusty main" | sudo tee "/etc/apt/sources.list.d/mrt.list" > /dev/null

#install build system stuff
RUN sudo apt-get update && sudo apt-get install -y cmake git

#install python stuff
RUN sudo apt-get update && sudo apt-get install -y python-yaml python-pip --yes

#install mrt build system related stuff
RUN sudo pip install pyapi-gitlab colorama
RUN sudo apt-get update && sudo apt-get install -y mrt-cmake-modules mrt-build

RUN sudo echo "yaml file:///mrtsoftware/pkg/share/ros/base.yaml" | sudo tee --append "/etc/ros/rosdep/sources.list.d/20-default.list" > /dev/null

# grab gosu for easy step-down from root
RUN gpg --keyserver pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN apt-get update && apt-get install -y curl \
	&& curl -o /usr/local/bin/gosu -SL "https://github.com/tianon/gosu/releases/download/1.6/gosu-$(dpkg --print-architecture)" \ 
	&& curl -o /usr/local/bin/gosu.asc -SL "https://github.com/tianon/gosu/releases/download/1.6/gosu-$(dpkg --print-architecture).asc" \ 
	&& gpg --verify /usr/local/bin/gosu.asc \ 
	&& rm /usr/local/bin/gosu.asc \ 
	&& chmod +x /usr/local/bin/gosu

COPY files/* /tmp/userFiles/
