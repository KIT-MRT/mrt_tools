import subprocess
import os
import pwd
import grp


def pkg(package_name):
    _start_docker("mrt_build_check_pkg", [package_name])


def ws(workspace_folder, build_parameters = []):
    _start_docker("mrt_build_check_ws", [workspace_folder] + build_parameters)


def _start_docker(docker_name, parameters):
    user_data = pwd.getpwuid(os.getuid())
    group_data = grp.getgrgid(user_data.pw_gid)
    user_parameters = [str(user_data.pw_uid), user_data.pw_name, str(user_data.pw_gid), group_data.gr_name]

    # build docker command line
    cuda_device_string = ["--device", "/dev/nvidia0:/dev/nvidia0",
                          "--device", "/dev/nvidiactl:/dev/nvidiactl",
                          "--device", "/dev/nvidia-uvm:/dev/nvidia-uvm"]

    exec_string = ["docker", "run", "-ti"] + cuda_device_string + ["--rm=true", docker_name] + \
                  user_parameters + parameters

    # execute docker
    print(exec_string)
    subprocess.check_call(exec_string)