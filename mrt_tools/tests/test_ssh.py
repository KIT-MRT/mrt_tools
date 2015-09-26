from click.testing import CliRunner
from mrt_tools.base import SSHkey
from mrt_tools.settings import *
import pytest
import os


# TODO write tests
@pytest.fixture
def runner():
    return CliRunner()


def test_create_sshkey_default(runner):
    with runner.isolated_filesystem():
        curr_dir = os.getcwd()
        ssh = SSHkey(dir_path=curr_dir)
        ssh.create()
        assert os.path.isfile(os.path.join(curr_dir, default_ssh_key_name))
        assert os.path.isfile(os.path.join(curr_dir, default_ssh_key_name + ".pub"))


def test_create_sshkey_custom_name(runner):
    with runner.isolated_filesystem():
        curr_dir = os.getcwd()
        ssh = SSHkey(name="testkey", dir_path=curr_dir)
        ssh.create()
        assert os.path.isfile(os.path.join(curr_dir, "testkey"))
        assert os.path.isfile(os.path.join(curr_dir, "testkey.pub"))


def test_load_sshkey(runner):
    with runner.isolated_filesystem():
        curr_dir = os.getcwd()
        ssh = SSHkey(dir_path=curr_dir)
        ssh.create()
        ssh2 = SSHkey(dir_path=curr_dir)
        ssh2.load()
        assert ssh.public_key == ssh2.public_key
