#!/bin/bash

SELF="$(readlink /proc/$$/fd/255)" || SELF="$0" # Eigener Pfad (besseres $0)
SELF_DIR=$(dirname "${SELF}")

for installed_file in $(cat $SELF_DIR/../debian/mrt-build.links | cut -d " " -f 1); do
	git_file=$(basename "${installed_file}")
	sudo rm $installed_file
	sudo ln -s $SELF_DIR/$git_file $installed_file
	echo "Linking $git_file"
done