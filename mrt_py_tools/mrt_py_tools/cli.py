import click
import os

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')


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
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['main']


cli = MyCLI(help='A toolbelt full of mrt scripts.')

if __name__ == '__main__':
    cli()

# TODO add source setup.bash to bashrc when installing

