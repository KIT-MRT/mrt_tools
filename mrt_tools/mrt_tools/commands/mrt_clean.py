import os
import shutil
from mrt_tools.base import Workspace
import click


@click.command()
def main():
    ws = Workspace()
    ws.test_for_changes()
    ws.cd_root()
    current_path = os.getcwd()
    click.confirm("Delete everything within " + current_path, abort=True)
    file_list = [f for f in os.listdir(".")]
    for f in file_list:
        if os.path.isdir(f):
            shutil.rmtree(f)
        else:
            os.remove(f)
