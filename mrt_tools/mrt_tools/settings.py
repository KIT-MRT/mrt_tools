#!/usr/bin/python

# Default settings

# Token
default_token_path = "~/.mrtgitlab/.token"

# SSH Keys
default_ssh_path = "~/.ssh"
default_ssh_key_name = "mrtgitlab"

# Cache
default_repo_cache = "~/.mrtgitlab/repo_cache"
default_cache_lock = "~/.mrtgitlab/.repo_cache_lock"
default_repo_cache_decay_time = 5*60  # in seconds
default_cache_lock_decay_time = 30  # in seconds

# Gitlab
default_host = "https://gitlab.mrt.uni-karlsruhe.de"

# Snapshot
file_ending = ".snapshot"
snapshot_version = "0.1.0"
version_file = "snapshot.version"
