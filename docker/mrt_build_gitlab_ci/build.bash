#!/bin/bash
echo "WARNING: Your credentials will be stored in this docker image."
echo "*****FOR PERSONAL USE ONLY*****"
read -s -p "Enter Password: " mypassword
docker build --build-arg user=$USER --build-arg pw=$mypassword --force-rm --no-cache $1 -t mrt_build_gitlab_ci .
