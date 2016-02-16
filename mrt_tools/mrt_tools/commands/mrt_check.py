from mrt_tools.Workspace import Workspace

import paramiko
import getpass
import os
import sys
import time
import fcntl
import termios
import tarfile
import tempfile
import stat
import mrt_tools.DockerCheck

import click

@click.group()
def main():
    pass

@main.command(short_help="Tests a workspace in a clean environment.",
              help="Builds a workspace on mrtknecht or local in a docker environment. "
                   "All non hidden files of the src folder are transfered to the docker "
                   "and copied to a newly created catkin workspace. Then a release build "
                   "is performed."
                   "It can be used without pushing your source files to git.")
@click.option('--local', is_flag=True, help='Test locally instead on mrtknecht '
                                            '(docker environment must be setup properly).')
def ws(local):
    ws = Workspace()
    ws_root = ws.get_root()
    ws_src = os.path.join(ws_root, "src")
    if not os.path.exists(ws_src):
        raise "Cannot find workspace source folder"

    if local:
        mrt_tools.DockerCheck.ws(ws_root)
        return

    ssh = _connect()

    #copy data to server
    sftp = ssh.open_sftp()

    #create docker folder if not exist
    sftp.chdir("/tmp")
    if not "docker" in sftp.listdir():
        sftp.mkdir("docker")

    sftp.chmod("docker", mode = stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    sftp.chdir("docker")

    #create temporary file and create tar archive
    try:
        tarPathName = tempfile.mkstemp()[1]
        tarFile = tarfile.TarFile(tarPathName, "w")

        tempFileName = os.path.basename(tarPathName)
        remote_work_dir = os.path.join("/tmp", "docker", tempFileName)
        
        #prepare wokspace
        sftp.mkdir(tempFileName, mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        _executeSshCommand(ssh, 'bash -c "cd {0} && mrt ws init"'.format(remote_work_dir))
        
        os.chdir(ws_src)
        tarFile.add(".", exclude=lambda p: os.path.basename(os.path.abspath(p)).startswith('.'))
        tarFile.close()

        #copy tar archive to remote
        dest_tar = os.path.join(remote_work_dir, tempFileName + ".tar")
        sftp.put(tarPathName, dest_tar)
    finally:
        if os.path.exists(tarPathName):
            os.remove(tarPathName)

    sftp.close()

    remote_work_src = os.path.join(remote_work_dir, "src")
    ssh.exec_command("tar -xf " + dest_tar + " -C " + remote_work_src)
    ssh.exec_command("rm " + dest_tar)

    #run docker build
    execLine = 'bash -c "cd {0}  && mrt check ws --local"'.format(remote_work_dir)
    _executeSshCommand(ssh, execLine)


@main.command(short_help="Tests a package in a clean environemnt.",
              help="The specified package will be checked out out from git in a " 
                   "docker environment. All dependencies are resolved and a "
                   "release build is performed.")
@click.argument('pkg_name', type=click.STRING, required=True)
@click.option('--local', is_flag=True, help='Test locally instead on mrtknecht '
                                            '(docker environment must be setup properly).')
def pkg(pkg_name, local):
    if local:
        mrt_tools.DockerCheck.pkg(pkg_name)
        return

    ssh = _connect()

    execLine = 'mrt check pkg {0} --local'.format(pkg_name)

    _executeSshCommand(ssh, execLine)


def _connect():
    #connect to server per ssh
    print("Connect to mrtknecht")
    ssh = paramiko.client.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect('mrtknecht', gss_auth=True, gss_kex=True)
    except paramiko.ssh_exception.SSHException:
        ssh.connect('mrtknecht', username=getpass.getuser(), password=getpass.getpass())

    return ssh

def _executeSshCommand(ssh, execCommand):
    #execute
    transport = ssh.get_transport()
    session = transport.open_session()
    session.get_pty()
    session.exec_command(execCommand)

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)

    try:
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ECHO          # lflags
        new[3] = new[3] & ~termios.ICANON

        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        nbytes = 4096
        sleep = True
        while True:
            #handle output
            if session.recv_ready():
                sys.stdout.write(session.recv(nbytes))
                sys.stdout.flush()
                sleep = False
            if session.recv_stderr_ready():
                sys.stderr.write(session.recv_stderr(nbytes))
                sys.stderr.flush()
                sleep = False

            #handle input
            try:
                session.sendall(os.read(fd, 1))
            except:
                sleep = True

            #check if command is done
            if session.exit_status_ready():
                break

            #sleep if no input or output occurs
            if sleep:
                time.sleep(0.001)
            else:
                sleep = True

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
