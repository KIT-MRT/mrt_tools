from mrt_tools.utilities import *
from mrt_tools.base import *
import click


########################################################################################################################
# Gitlab
########################################################################################################################
@click.group()
def main():
    """Gitlab related tools"""
    pass


@main.command()
def create_token():
    """Create new gitlab token"""
    Token(allow_creation=True)


@main.command()
def create_ssh_key():
    """Create new ssh key"""
    SSHkey().create()


@main.command()
@click.argument("pkg_name", type=click.STRING, required=False)
def create_repo(pkg_name):
    """Create new gitlab token"""
    ws = Workspace()
    ws.recreate_index(write=True)
    pkg_list = ws.get_catkin_package_names()
    pkg_dicts = ws.get_wstool_packages()
    if not pkg_name:
        pkg_name = os.path.basename(ws.org_dir)

    if pkg_name not in pkg_list:
        click.secho("{0} does not seem to be a catkin package.".format(pkg_name), fg="red")
        sys.exit(1)

    click.echo("Creating repo for {0}".format(pkg_name))
    for ps in ws.wstool_config.get_config_elements():
        if ps.get_local_name() == pkg_name:
            click.secho("Repository has a url already: {0}".format(ps.get_path_spec().get_uri()))
            sys.exit(1)

    ws.cd_src()
    os.chdir(pkg_name)
    git = Git()
    ssh_url = git.create_repo(pkg_name)
    subprocess.call("git init", shell=True)
    subprocess.call("git remote add origin " + ssh_url + " >/dev/null 2>&1", shell=True)
    ws.recreate_index()
    click.echo("You should run 'mrt fix url_in_package_xml' now")


########################################################################################################################
# Permissions
########################################################################################################################
@main.group()
@click.pass_context
def permissions(ctx):
    """Tools for handling permissions..."""
    ctx.obj = Git()


@permissions.command()
@click.pass_obj
def add_user(git):
    """Add a user to a repository"""
    click.echo("Loading... please wait a moment")

    users = list(git.server.getall(git.server.getusers))
    users = sorted(users, key=lambda k: k['name'])
    repo_dicts = git.get_repos()
    repo_dicts = sorted(repo_dicts, key=lambda k: k['path_with_namespace'])
    user_choice = get_user_choice([user["name"] for user in users], prompt="Please choose a user")
    user = users[user_choice[0]]
    repo_choice = get_user_choice([repo["path_with_namespace"] for repo in repo_dicts], prompt="Please choose a repo.")
    repo = repo_dicts[repo_choice[0]]
    roles = ["Guest", "Reporter", "Developer", "Master", "Owner"]
    role_choice = get_user_choice(roles, prompt='Please choose a role for the user.', default=2)

    click.echo("\nAdding user {0} to repo {1} with role {2}\n".format(user["name"].upper(),
                                                                      repo["path_with_namespace"].upper(),
                                                                      role_choice[1].upper()))
    git.server.addprojectmember(repo["id"], user["id"], role)
    if not click.confirm("Should I test dependencies?", default=True):
        return

    # Create temporary workspace
    org_dir = os.getcwd()
    if os.path.exists("/tmp/mrtgitlab_test_ws"):
        shutil.rmtree("/tmp/mrtgitlab_test_ws")
    os.mkdir("/tmp/mrtgitlab_test_ws")
    os.chdir("/tmp/mrtgitlab_test_ws")
    ws = Workspace(silent=True)
    ws.create()

    # Clone pkg and resolve dependencies
    pkg_name = repo["name"]
    url = git.find_repo(pkg_name)  # Gives error string
    ws.add(pkg_name, url)
    ws.resolve_dependencies(git=git)

    # Read in dependencies
    ws.load()
    new_repos = ws.get_catkin_packages()
    new_repos.pop(pkg_name)
    click.echo("\n\nFound following new repos:")
    for r in new_repos:
        click.echo(r)
    if not click.confirm("\nAdd user {0} to these repos aswell?".format(user["name"]), default=True):
        return
    for r in new_repos:
        click.echo("\nAdding user {0} to repo {1}\n".format(user["name"].upper(),
                                                            r.upper()))
        repo_id = [s["id"] for s in repo_dicts if s["name"] == r]
        role_choice = get_user_choice(roles, prompt='Please choose a role for the user for this repo.', default=2)
        git.server.addprojectmember(repo_id[0], user["id"], role_choice[1])

    # Add user as well
    os.chdir(org_dir)
    shutil.rmtree("/tmp/mrtgitlab_test_ws")


# @permissions.command()
# @click.pass_obj
# def add_group(git):
#     pass
#

########################################################################################################################
# List
########################################################################################################################
@main.group()
@click.pass_context
def show(ctx):
    """Display a list of..."""
    ctx.obj = Git()


@show.command()
@click.pass_obj
def users(git):
    """Display a list of user names"""
    user_list = list(git.server.getall(git.server.getusers, per_page=100))
    user_list = sorted(user_list, key=lambda k: k['name'])
    for index, item in enumerate(user_list):
        click.echo("(" + str(index) + ") " + item['name'])


@show.command()
@click.pass_obj
def repos(git):
    """Display a list of repositories"""
    repo_list = list(git.server.getall(git.server.getprojects, per_page=100))
    repo_list = sorted(repo_list, key=lambda k: k['name'])
    for index, item in enumerate(repo_list):
        click.echo("(" + str(index) + ") " + item['name'])


@show.command()
@click.pass_obj
def groups(git):
    """Display a list of user names"""
    group_list = list(git.server.getall(git.server.getgroups, per_page=100))
    group_list = sorted(group_list, key=lambda k: k['name'])
    for index, item in enumerate(group_list):
        click.echo("(" + str(index) + ") " + item['name'])


@show.command()
@click.pass_obj
def namespaces(git):
    """Display a list of available namespaces"""
    # ns_list = list(git.server.getall(git.server.getgroups, per_page=100))
    # ns_list = sorted(ns_list, key=lambda k: k['name'])
    # user_name = git.server.currentuser()['username']
    # if user_name not in ns_list:
    #     ns_list.append({'name': user_name, 'id': 0})
    ns_list = git.get_namespaces()
    for index, item in enumerate(ns_list):
        click.echo("(" + str(index) + ") " + item)
