#!/usr/bin/python
import getpass
import gitlab
import os

# ###############################
# # GitLab Client Setup Utility #
# ###############################
# This tool interactively runs you through the GitLab client setup of your computer. 

# Define paths
token_dir = os.path.expanduser("~/.mrtgitlab")
token_file = token_dir+"/.token"
host = "https://gitlab.mrt.uni-karlsruhe.de"

# Check for token file
if os.path.isfile(token_file):
	print("Private token file exists already.")
	token = os.read(os.open(token_file,0),20)
	git = gitlab.Gitlab(host, token=token)
else:
	print("No token file found. Fetching token from gitlab")
	username = raw_input("Gitlab user name: ")
	password = getpass.getpass()
	git = gitlab.Gitlab(host)
	git.login(username, password)
	gitlabuser = git.currentuser()
	token = gitlabuser['private_token']
	# Write to file
	if not os.path.exists(token_dir):
		os.mkdir(token_dir)
	os.mknod(token_file)
	os.write(os.open(token_file,1),token)
	print("Wrote token to file")