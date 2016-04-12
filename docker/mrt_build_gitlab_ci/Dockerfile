FROM mrt_build_dev:latest

# Pass user variables
ENV MRT_USERNAME <YOUR_USERNAME>
ENV MRT_PASSWORD <YOUR_PASSWORD>
ENV MRT_USER_ID  <YOUR_USERID>


# Create new user and
RUN echo "$MRT_USERNAME    ALL = NOPASSWD: /usr/bin/apt-get" | sudo tee -a /etc/sudoers &> /dev/null \
    && addgroup -q --gid $MRT_USER_ID $MRT_USERNAME \
    && useradd -ms /bin/bash --gid $MRT_USER_ID --uid $MRT_USER_ID $MRT_USERNAME

# Setup config files for new user
COPY files/mrt.cfg /home/$MRT_USERNAME/.mrtgitlab/mrt.cfg
RUN mkdir -p ~/.mrtgitlab/ \
		&& cp /tmp/userFiles/gitconfig /home/$MRT_USERNAME/.gitconfig \
    && chown -R $MRT_USERNAME:$MRT_USERNAME /home/$MRT_USERNAME

# Change user
USER $MRT_USERNAME
WORKDIR /home/$MRT_USERNAME

# Create initial workspace, trigger rosdep update and make sure credentials were passed.
RUN /bin/bash -c "source /opt/ros/$ROS_DISTRO/setup.bash \
    && mkdir -p ~/workspace/src \
    && cd ~/workspace \
    && catkin init \
    && mrt maintenance credentials update_cache \
    && mrt ws resolve_deps"
