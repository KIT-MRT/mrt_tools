#!/usr/bin/python
import getpass
import gitlab
import os
import distutils.util
import sys

# Define paths
token_dir = os.path.expanduser("~/.mrtgitlab")
token_file = token_dir + "/.token"
host = "https://gitlab.mrt.uni-karlsruhe.de"


def createGitlabTokenFile():
    username = raw_input("Gitlab user name: ")
    password = getpass.getpass()
    git = gitlab.Gitlab(host)
    git.login(username, password)
    gitlabuser = git.currentuser()
    token = gitlabuser['private_token']

    # Write to file
    if not os.path.exists(token_dir):
        os.mkdir(token_dir)

    if not os.path.isfile(token_file):
        os.mknod(token_file)
    os.write(os.open(token_file, 1), token)


def checkForTokenFile():
    # Check for token file
    create_new_token = True
    if os.path.isfile(token_file):
        # print("Private token file exists already.")
        # choice_str = raw_input("Would you like to recreate it [y/N]? ")
        # if choice_str == "":
        #     choice_str = "n"
        #
        # create_new_token = distutils.util.strtobool(choice_str)
        create_new_token = False

    if create_new_token:
        for i in range(0, 3):
            try:
                createGitlabTokenFile()
                break
            except:
                print("Cannot connect to gitlab server. Try again")


def checkSSHkey():
    exit_code = os.system(
        'ssh -T -o "StrictHostKeyChecking=no" -o "BatchMode=yes" -o "ConnectTimeout=3" git@gitlab.mrt.uni-karlsruhe.de > /dev/null 2>&1')  # check for ssh key
    if exit_code is not 0:
        print "Your SSH Key does not seem to work. Have you created one and added it to gitlab?";
        sys.exit(1);


def connect():
    checkSSHkey()
    checkForTokenFile()
    # Connect
    token = os.read(os.open(token_file, 0), 20)
    git = gitlab.Gitlab(host, token=token)
    return git


def getNamespaces():
    # Check namespaces
    git = connect()
    namespaces = {project['namespace']['name']: project['namespace']['id'] for project in git.getall(git.getprojects)}
    if git.currentuser()['username'] not in namespaces.keys():
        namespaces[
            git.currentuser()['username']] = 0  # The default user namespace_id will be created with first userproject
    return namespaces


def getRepos():
    # Check wether repo exists
    # Get all repos and clone them
    git = connect()
    return git.getall(git.getprojects)

def findRepo(repo_name):
    # Check wether repo exists
    # Get all repos and clone them
    git = connect()
    #TODO Return only url
    #TODO Ask user if multiple were found
    return git.getall(git.searchproject(repo_name))
