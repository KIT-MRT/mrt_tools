FROM mrt_build_dev:latest

ARG user
ARG pw

# Create new user and Setup config files for new user
RUN echo "$user    ALL = NOPASSWD: /usr/bin/apt-get" | sudo tee -a /etc/sudoers &> /dev/null \
    && useradd -ms /bin/bash $user\
    && mkdir -p /workspace/src \
    && mkdir -p /home/$user/.mrtgitlab/ \
		&& cp /tmp/userFiles/gitconfig /home/$user/.gitconfig \
		&& cp /tmp/userFiles/mrt.cfg /home/$user/.mrtgitlab/mrt.cfg \
    && chown -R $user:$user /home/$user \
    && chown -R $user:$user /workspace

VOLUME ["/workspace"]

# Change user
USER $user
WORKDIR /workspace

# Create initial workspace, trigger rosdep update and make sure credentials were passed.
RUN /bin/bash -c "source /opt/ros/$ROS_DISTRO/setup.bash \
    && mrt maintenance credentials set $user $pw \
    && catkin init \
    && mrt maintenance credentials update_cache \
    && mrt ws resolve_deps"
