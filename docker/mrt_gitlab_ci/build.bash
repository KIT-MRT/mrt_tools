#!/bin/bash
echo "WARNING: Your credentials will be stored in this docker image."
read -p "Enter Username: " username
read -s -p "Enter Password: " mypassword
docker build --build-arg user=$username --build-arg pw=$mypassword --force-rm $1 -t mrt_gitlab_ci .
