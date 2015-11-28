#!/usr/bin/python

import paramiko
import getpass
import tempfile
import os
import tarfile
import stat
import sys
import time
import select

if len(sys.argv) < 3:
    print("Usage: docker_mrt_check_ws [token file name] [workspace src dir] <build parameters>")
    sys.exit(1)

tokenFileName = os.path.abspath(sys.argv[1])
workspaceSrc = os.path.abspath(sys.argv[2])
parameters = ' '.join(sys.argv[3:])

if not os.path.isfile(tokenFileName):
    raise RuntimeError("Token file does not exist.")
    sys.exit(1)
    
if not os.path.isdir(workspaceSrc):
    raise RuntimeError("Source folder does not exist.")
    sys.exit(1)

docker_script_path = "/mrtsoftware/scripts/docker_check_ws.py"

#get ssh password
p = getpass.getpass()

#connect to server per ssh
ssh = paramiko.client.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('mrtknecht', username=getpass.getuser(), password=p)

#copy data to server
sftp = ssh.open_sftp()

#create docker folder if not exist
sftp.chdir("/tmp")
if not "docker" in sftp.listdir():
    sftp.mkdir("docker")

sftp.chmod("docker", mode = stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
sftp.chdir("docker")

#create temporary file and create tar archive
tarPathName = tempfile.mkstemp()[1]
tarFile = tarfile.TarFile(tarPathName, "w")

tempFileName = os.path.basename(tarPathName)
sftp.mkdir(tempFileName, mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

for root, dirs, files in os.walk(workspaceSrc):
    #do not copy hidden folders
    for dirName in dirs:
        if dirName.startswith('.'):
            dirs.remove(dirName)
    #add files to tar archive
    for fileName in files:
        if not fileName.startswith('.'):
            tarFile.add(os.path.join(root, fileName))

tarFile.close()

#copy tar archive to remote
destTar = os.path.join("/tmp", "docker", tempFileName, tempFileName + ".tar")
sftp.put(tarPathName, destTar)

#copy token file to remote
destToken = os.path.join("/tmp", "docker", tempFileName, ".token")

sftp.put(tokenFileName, destToken)

sftp.close()

#extract tar archive
stdcin, stdcout, stdcerr = ssh.exec_command("tar -xf " + destTar + " -C " + os.path.dirname(destTar))
stdcerr.readlines()

#run docker build
execLine = "python " + docker_script_path + " " + destToken + " " + os.path.dirname(destTar) + workspaceSrc + " " + parameters

#execute 
transport = ssh.get_transport()
session = transport.open_session()
session.get_pty()
session.exec_command(execLine)

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


