#!/usr/bin/python
import subprocess
import re
import sys
import os

if len(sys.argv) == 1 or len(sys.argv) > 5:
    print("Usage: mrt_check_pkg [private token] [package name] <url>")
    sys.exit(1)

tokenFileName = os.path.abspath(sys.argv[1])
parameters = sys.argv[2:]

if not os.path.isfile(tokenFileName):
    raise RuntimeError("Token file not found")

#get user name/id and group name/id
p = re.compile(r"uid=([0-9]+)\(([^\)]+)\) gid=([0-9]+)\(([^\)]+)\)")
userId = subprocess.check_output(["id"])
m = p.match(userId)
userParameters = list(m.group(1, 2, 3, 4))

#build docker command line
cudaDeviceString = ["--device", "/dev/nvidia0:/dev/nvidia0", "--device", "/dev/nvidiactl:/dev/nvidiactl", "--device", "/dev/nvidia-uvm:/dev/nvidia-uvm"]
mountScript = ["-v", tokenFileName + ":/tmp/.mrtgitlab/.token"]

execString = ["docker", "run", "-ti"] + cudaDeviceString + mountScript + ["--rm=true", "mrt_build_check_pkg"] + userParameters + parameters

#execute docker
subprocess.check_call(execString)

