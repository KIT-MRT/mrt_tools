FROM mrt_build_dev:latest

ARG user
ARG pw
ENV MRT_USERNAME $user
ENV MRT_PASSWORD $pw

# Install all mrt software
#RUN apt-get update && apt-get install mrt-* -y

# Create new user
RUN echo "$MRT_USERNAME    ALL = NOPASSWD: /usr/bin/apt-get" | sudo tee -a /etc/sudoers &> /dev/null \
    && useradd -ms /bin/bash $MRT_USERNAME\
    && mkdir -p /workspace/src

# Setup config files for new user
COPY files/mrt.cfg /home/$MRT_USERNAME/.mrtgitlab/mrt.cfg
RUN mkdir -p ~/.mrtgitlab/ \
		&& cp /tmp/userFiles/gitconfig /home/$MRT_USERNAME/.gitconfig \
    && chown -R $MRT_USERNAME:$MRT_USERNAME /home/$MRT_USERNAME \
    && chown -R $MRT_USERNAME:$MRT_USERNAME /workspace

VOLUME ["/workspace"]

# Change user
USER $MRT_USERNAME
WORKDIR /workspace


# Create initial workspace, trigger rosdep update and make sure credentials were passed.
RUN /bin/bash -c "source /opt/ros/$ROS_DISTRO/setup.bash \
    && catkin init \
    && mrt maintenance credentials update_cache \
    && mrt ws resolve_deps"
