#!/usr/bin/python
import subprocess
import re
import sys
import os
import pwd
import grp

if len(sys.argv) != 2:
    print("Usage: mrt_check_pkg [package name]")
    sys.exit(1)

parameters = sys.argv[1]

userData = pwd.getpwuid(os.getuid())
groupData = grp.getgrgid(p.pw_gid)
userParameters = [p.pw_uid, p.pw_name, p.pw_gid, groupData.gr_name]

#build docker command line
cudaDeviceString = ["--device", "/dev/nvidia0:/dev/nvidia0", "--device", "/dev/nvidiactl:/dev/nvidiactl", "--device", "/dev/nvidia-uvm:/dev/nvidia-uvm"]

execString = ["docker", "run", "-ti"] + cudaDeviceString + ["--rm=true", "mrt_build_check_pkg"] + userParameters + parameters

#execute docker
subprocess.check_call(execString)

