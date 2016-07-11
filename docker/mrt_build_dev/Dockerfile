FROM mrt_build:latest

# Install from local version
RUN apt-get update && apt-get install -y libyaml-dev libpython2.7-dev libffi-dev nano tree
COPY files/* /usr/local/src/mrt_build/
RUN pip install -U -I -r /usr/local/src/mrt_build/requirements.txt
RUN cd /usr/local/src/mrt_build/ && python setup.py develop

# Create known_hosts and add server key
RUN mkdir -p /root/.ssh \
    && touch /root/.ssh/known_hosts \
    && ssh-keyscan gitlab.mrt.uni-karlsruhe.de >> /root/.ssh/known_hosts
