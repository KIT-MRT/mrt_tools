FROM mrt_build:latest

# Install from local version
RUN apt-get update && apt-get install -y libyaml-dev libpython2.7-dev
COPY files/mrt_tools /root/mrt_tools
RUN pip install -I -r /root/mrt_tools/requirements.txt \
		&& cd /root/mrt_tools \
		&& python setup.py install \
		&& cp /usr/local/bin/mrt /usr/bin/mrt

# Create known_hosts and add server key
RUN mkdir -p /root/.ssh \
    && touch /root/.ssh/known_hosts \
    && ssh-keyscan gitlab.mrt.uni-karlsruhe.de >> /root/.ssh/known_hosts
