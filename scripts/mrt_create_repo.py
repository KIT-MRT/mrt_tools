#!/usr/bin/python
import getpass
import gitlab
import sys
import os

# ###################################
# # GitLab Repository Setup Utility #
# ###################################
# This tool creates a new GitLab repository on the server

def main(repo_name): 
	# Define paths
	token_dir = os.path.expanduser("~/.mrtgitlab")
	token_file = token_dir+"/.token"
	host = "https://gitlab.mrt.uni-karlsruhe.de"

	# Check for token file
	if not os.path.isfile(token_file):
		import mrt_setup_gitlab # path to script?

	# Connect
	token = os.read(os.open(token_file,0),20)
	git = gitlab.Gitlab(host, token=token)

	# Check wether repo exists
	# Get all repos and clone them
	for project in git.getall(git.getprojects):
		if project['name'] == repo_name:
			print >> sys.stderr, "    ERROR Repo exist already: "+project['ssh_url_to_repo']
			print ""
			exit()

	# Create repo
	request = git.createproject(repo_name, namespace_id="7")
	if not request:
		print >> sys.stderr, "There was a problem with creating the repo."
		print ""
		exit()
	
	# Return URL
	print request['ssh_url_to_repo']

	
if __name__ == '__main__':
    repo_name = sys.argv[1]
    main(repo_name) 
