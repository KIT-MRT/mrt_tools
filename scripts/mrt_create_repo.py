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
        os.system("mrt_setup_gitlab")

	# Connect
	token = os.read(os.open(token_file,0),20)
	git = gitlab.Gitlab(host, token=token)

    # Check namespaces
    namespaces = {project['namespace']['name']: project['namespace']['id'] for project in git.getall(git.getprojects)}
    if git.currentuser()['username'] not in namespaces.keys():
        namespaces[git.currentuser()['username']] = 0   # The default user namespace_id will be created with first userproject

    # Dialog to choose namespace
    print "Available namespaces in gitlab:"
    for index, item in enumerate(namespaces):
        print "(" + str(index) + ") " + item
    valid_choices = {str(x) for x in range(0, len(namespaces))}
    while True:
        user_choice = str(raw_input("Please select on of the above namespaces for your new project: "))
        if user_choice in valid_choices:
            break
    print "Using namespace '" + namespaces.keys()[int(user_choice)] + "'"
    ns_id = namespaces.values()[int(user_choice)]

    # Check wether repo exists
    # Get all repos and clone them
    for project in git.getall(git.getprojects):
        if project['namespace']['id'] == ns_id and project['name'] == repo_name:
            print >> sys.stderr, "    ERROR Repo exist already: " + project['ssh_url_to_repo']
            print ""
            exit()

    # Create repo
    if ns_id == 0:  # Create new user namespace
        request = git.createproject(repo_name)
    else:
        request = git.createproject(repo_name, namespace_id=ns_id)
    if not request:
        print >> sys.stderr, "There was a problem with creating the repo."
        print ""
        exit()
	
	# Return URL
	print request['ssh_url_to_repo']

	
if __name__ == '__main__':
    repo_name = sys.argv[1]
    main(repo_name) 
