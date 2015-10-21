#!/usr/bin/python
import subprocess
import re
import sys
import os

if len(sys.argv) < 3:
    print("Usage: docker_mrt_check_ws [token file name] [workspace src dir] <build parameters>")
    sys.exit(1)

tokenFileName = os.path.abspath(sys.argv[1])
workspaceSrc = os.path.abspath(sys.argv[2])
parameters = sys.argv[3:]

#get user name/id and group name/id
p = re.compile(r"uid=([0-9]+)\(([^\)]+)\) gid=([0-9]+)\(([^\)]+)\)")
userId = subprocess.check_output(["id"])
m = p.match(userId)
userParameters = list(m.group(1, 2, 3, 4))

#build docker command line
cudaDeviceString = ["--device", "/dev/nvidia0:/dev/nvidia0", "--device", "/dev/nvidiactl:/dev/nvidiactl", "--device", "/dev/nvidia-uvm:/dev/nvidia-uvm"]
mountScript = ["-v", tokenFileName + ":/tmp/.mrtgitlab/.token", "-v", workspaceSrc + ":/tmp/ws/src:ro"]

execString = ["docker", "run", "-ti"] + cudaDeviceString + mountScript + ["--rm=true", "mrt_build_check_ws"] + userParameters + parameters

#execute docker
subprocess.check_call(execString)

