from mrt_tools.RosbagMetadataHandler import RosbagMetadataHandler
from mrt_tools.utilities import get_help_text
import subprocess
import time
import click
import os

try:
    import rospy
    topic_list = rospy.get_published_topics()
    topic_list = [pair[0][1:] for pair in topic_list]
except:
    topic_list = []


@click.group(short_help="A wrapper for rosbag.",
             help="This group of commands wrap the native 'rosbag' command. The original commands are extanded by "
                  "forcing the user to specify more metadata when recording a rosbag. The data is stored in a seperate "
                  "topic inside the rosbag.")
def main():
    pass


@main.command(context_settings=dict(ignore_unknown_options=True, ), short_help="Record a new annotated rosbag.",
              help=get_help_text("rosbag record --help"))
@click.option('-O', '--output-name', 'output_name', type=click.STRING)
@click.option('-o', '--output-prefix', 'prefix', type=click.STRING)
@click.option('-r','--reuse', 'reuse', is_flag=True)
@click.argument('args', nargs=-1, type=click.UNPROCESSED, autocompletion=topic_list)
def record(output_name, prefix, reuse, args):
    if not [arg for arg in args if not arg.startswith("-")] and "-a" not in args:
        click.echo("You must specify a topic name or else use the '-a' option.")
        return

    # Determine file name
    if not output_name:
        output_name = time.strftime("%Y-%m-%d-%H-%M-%S.bag", time.localtime())
        if prefix:
            output_name = prefix + "_" + output_name
    if not output_name.endswith(".bag"):
        output_name += ".bag"
    args += ("-O", output_name)

    # Collect metadata
    rmh = RosbagMetadataHandler()
    rmh.collect_metadata(reuse_last=reuse)

    # Perform action
    process = subprocess.Popen(["rosbag", "record"] + list(args))
    try:
        process.wait()
    except KeyboardInterrupt:
        click.echo("")
        process.terminate()
        process.communicate()

    rmh.write_to_bag(output_name)


@main.command()
@click.argument('bagfile', type=click.STRING, required=True)
@click.option('--clean', 'clean', is_flag=True, help="Discard existing metadata")
def annotate(bagfile, clean):
    """Add metadata to an existing rosbag"""
    if not os.path.isfile(bagfile):
        click.echo("No such file: {}".format(os.path.abspath(bagfile)))
        return
    rmh = RosbagMetadataHandler()
    rmh.collect_metadata(bagfile, clean_start=clean)
    rmh.write_to_bag(bagfile)


@main.command(context_settings=dict(ignore_unknown_options=True, ), short_help="Show metadata of one or more bag files",
              help=get_help_text("rosbag info --help"))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def info(args):
    options = [arg for arg in args if arg.startswith("-")]
    bags = [arg for arg in args if not arg.startswith("-")]
    for bag in bags:
        if os.path.isdir(bag):
            click.echo("{} is not a rosbag".format(bag))
            continue
        click.echo("============ INFO for file {} ============".format(os.path.basename(bag)))
        rmh = RosbagMetadataHandler()
        rmh.data = rmh.load_from_bag(bag)
        if rmh.data is not None:
            click.echo(rmh)
            click.echo("Rosbag")
            click.echo("=" * len("Rosbag"))
            subprocess.call(["rosbag", "info"] + list(options) + [bag])
