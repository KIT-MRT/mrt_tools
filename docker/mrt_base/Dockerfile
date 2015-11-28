FROM ubuntu:14.04

RUN sudo apt-get update && sudo apt-get install -q -y \
	bash-completion \
	build-essential \
	wget \
	software-properties-common \
	python-software-properties

# Install cuda
WORKDIR /tmp
RUN sudo wget http://mrtfile2/tms/NVIDIA-Linux-x86_64-349.16.run && \
	sudo wget http://mrtfile2/tms/cuda_7.0.28_linux.run && \
	sudo chmod +x *.run && \
	sudo ./NVIDIA-Linux-x86_64-349.16.run -s -N --no-kernel-module && \
	sudo ./cuda_7.0.28_linux.run --toolkit --verbose --silent && \
	sudo rm -r /usr/local/cuda-7.0/samples && \
	sudo rm /tmp/NVIDIA-Linux-x86_64-349.16.run /tmp/cuda_7.0.28_linux.run

ENV LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-7.0/lib64
ENV PATH=$PATH:/usr/local/cuda-7.0/bin

# Install g++4.9 and gcc4.9
RUN sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test && \
	sudo apt-get update && sudo apt-get install -q -y \
	g++-4.9 \
	gcc-4.9 && \
	sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.9 60 --slave /usr/bin/g++ g++ /usr/bin/g++-4.9

#Set locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
