from mrt_tools.utilities import *
import pytest
import os


@pytest.fixture(scope="module")
def working_directory(request):
    import tempfile
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    os.chdir(t)

    def fin():
        print ("Removing temporary directory")
        os.chdir(cwd)
        try:
            import shutil
            shutil.rmtree(t)
        except (OSError, IOError):
            pass

    request.addfinalizer(fin)
    return t


def test_get_script_root():
    root = get_script_root()
    curr_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mrt_tools"))
    print curr_dir
    assert root == curr_dir


def test_touch(working_directory):
    os.chdir(working_directory)
    touch("test")
    assert os.path.exists("test")
    import time
    now = time.time()
    touch("test2", (now, now))
    # assert os.path.exists("test2")
    last_mod = os.path.getmtime("test2")
    last_access = os.path.getatime("test2")
    assert (last_mod - now) < 0.01
    assert (last_access - now) < 0.01


def test_find_by_pattern(working_directory):
    os.chdir(working_directory)
    os.makedirs("dir1/dir2/dir3")
    os.makedirs("dir1/dir2/dir4")
    touch("dir1/abc.test")
    touch("dir1/aasf.py")
    touch("dir1/dir2/dir3/lkj.test")
    touch("dir1/dir2/dir4/slkj.cfg")
    test_files = find_by_pattern("*.test", os.getcwd())
    correct_files = [os.path.join(os.getcwd(), "dir1/abc.test"),
                     os.path.join(os.getcwd(), "dir1/dir2/dir3/lkj.test")]
    assert test_files == correct_files

# Untested functions
# def get_userinfo():
#     return
# def get_user_choice(items, extra=None, prompt="Please choose a number", default=None):
#     return
# def update_apt_and_ros_packages():
#     return
# def zip_files(files, archive):
#     return
# def check_naming(pkg_name):
#     return
# def get_rosdeps():
#     return
# def create_directories(pkg_name, pkg_type, ros):
#     return
# def create_cmakelists(pkg_name, pkg_type, ros, self_dir):
#     return
# def create_files(pkg_name, pkg_type, ros):
#     return
# def check_and_update_cmakelists(pkg_name, current_version):
#     return
# def set_eclipse_project_setting(ws_root):
#     return
# def cache_repos():
#     return
# def set_git_credentials(username, password):
#     return
# def test_git_credentials():
#     return