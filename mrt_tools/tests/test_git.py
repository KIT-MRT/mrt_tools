import os
import time

from mrt_tools.Git import Git, SSHkey, test_git_credentials
from mrt_tools.settings import user_settings
from mrt_tools import CredentialManager as cm
import pytest
import click

global user_settings
global credentialManager


def test_setup_git():
    cm.credentialManager = cm.BaseCredentialManager()
    cm.credentialManager.store("username", "root")
    cm.credentialManager.store("password", "gitlab_root")
    user_settings['Gitlab']['HOST_URL'] = "http://localhost:10080"

    git = Git(quiet=True)
    assert cm.credentialManager.get_token() is not None

    # Cleanup
    repos = git.get_repos()
    for repo in repos:
        git.server.deleteproject(repo["id"])
    keys = git.server.getsshkeys()
    for key in keys:
        git.server.deletesshkey(key["id"])


    # Test read operations
    assert git.get_namespaces() == {"root": 0}
    assert git.find_repo("testrepo") is None

    # Create a repo
    time.sleep(1)
    click.prompt = lambda text, default=None, hide_input=False, confirmation_prompt=False, type=None, \
                          prompt_suffix=': ', value_proc=None, show_default=True, err=False: 0
    assert git.create_repo("testrepo") == "http://localhost:10080/root/testrepo.git"
    assert git.find_repo("testrepo") is not None

    # Test ssh
    assert git.check_ssh_key() is False
    git.ssh_key = SSHkey(name="mrt_test_key")
    if os.path.exists(git.ssh_key.path):
        os.remove(git.ssh_key.path)
    git.ssh_key.create()
    git.upload_ssh_key()
    assert git.check_ssh_key() is True

    # Test git credential cache
    test_git_credentials()


if __name__ == '__main__':
    test_setup_git()
    # raise RuntimeError("USername {}, password {}".format(username,password))
