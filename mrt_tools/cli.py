from mrt_tools.settings import user_settings
import mrt_tools.commands
import os
import click
import sys

# Test for sudo
if os.getuid() == 0:
    if not user_settings['Other']['ALLOW_ROOT']:
        click.secho("Should not be run as root. Please use without sudo.", fg="red")
        sys.exit(0)

# Activate virtualenv if found
venv_activate_file = None
current_dir = os.path.dirname(os.path.realpath(__file__))
while current_dir != "/" and current_dir != "":
    file_path = os.path.join(current_dir, "bin", "activate_this.py")
    if os.path.isfile(file_path):
        venv_activate_file = file_path
        break
    current_dir = os.path.dirname(current_dir)
if venv_activate_file:
    execfile(venv_activate_file, dict(__file__=venv_activate_file))

# Load commands
plugin_folder = os.path.dirname(mrt_tools.commands.__file__)


class MyCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.startswith('mrt_') and filename.endswith('.py'):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, 'mrt_' + name + '.py')
        try:
            with open(fn) as f:
                code = compile(f.read(), fn, 'exec')
                eval(code, ns, ns)
        except IOError:
            click.secho("No such subcommand: '{0}'".format(name), fg="red")
            sys.exit(1)
        return ns['main']


cli = MyCLI(help='A toolbelt full of mrt scripts.')

if __name__ == '__main__':
    cli()
