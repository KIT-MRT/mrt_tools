from click.testing import CliRunner
from mrt_tools.base import SSHkey
from mrt_tools.settings import *
from mrt_tools import cli
import pytest
import os


# TODO write tests
@pytest.fixture
def runner():
    return CliRunner()


def test_create_workspace(runner):
    with runner.isolated_filesystem():
        curr_dir = os.getcwd()
        result = runner.invoke(cli, ["init_workspace"])
        assert not result.exception
        assert os.path.isdir(os.path.join(curr_dir, ".catkin_tools"))
        assert os.path.isfile(os.path.join(curr_dir, "src", ".rosinstall"))

