# Default settings
from mrt_tools.utilities import get_script_root
from mrt_tools.settings import CONFIG_DIR
from collections import OrderedDict
from unidecode import unidecode
import std_msgs
import getpass
import rosbag
import rospy
import click
import yaml
import time
import os

METADATA_CACHE = os.path.join(CONFIG_DIR, "rosbag_metadata.yaml")
DEFAULT_TOPIC = "/metadata"
METADATA_TEMPLATE = os.path.join(get_script_root(), "templates", "rosbag_metadata.yaml")


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """ Wrapper function to assert ordered loading of yaml file """

    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


# Represent OrderedDict as normal yaml when dumping to file or rosbag
yaml.add_representer(OrderedDict, lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items()))


class RosbagMetadataHandler(object):
    """
    This class handles metadata writing for rosbags

    Metadata takes the form of key-value pairs. Metadata can be nested in subcategories.
    The METADATA_TEMPLATE file specifies the minimal set of fields that have to be specified, but user defined fields
    can be added as desired.
    The data is stored in the topic "/metadata" of type std_msgs/String inside the rosbag.
    Additionally, a yaml file holding the last specified metadata is written to the local home folder,
    and is used for suggesting default values.
    """

    def __init__(self, ):
        """
        Constructor for RosbagHandler
        """
        self.data = None

    def __str__(self):
        """
        Represent this object as a string
        :return: Formatted string representation of data
        """
        if not self.data:
            return "\nNo custom metadata available.\n"
        return self.pretty(self.data)

    def pretty(self, data, indent=0):
        """
        Custom pretty print function for dictionaries
        :param data: Dictionary
        :param indent: How many tabs to print before this dict.
        :return: Formatted string representation of dict
        """
        output = "\n"
        for key, value in data.iteritems():
            if isinstance(value, dict):
                output += '\n' + '\t' * indent + str(key)
                output += '\n' + '\t' * indent + "=" * len(key)
                output += self.pretty(value, indent + 0)
            else:
                output += '\t' * indent + '{:12s} {}'.format(key + ":", value) + "\n"
        return output

    @staticmethod
    def load_from_file(filename):
        """
        Load yaml data from file into OrderedDict
        :param filename: Path to file
        :return: OrderedDict with key value pairs from file
        """
        if os.path.isfile(filename):
            return ordered_load(file(filename, 'r'))
        else:
            return OrderedDict()

    @staticmethod
    def write_to_file(filename, data):
        """
        Write Dictionary to file
        :param filename: Path to file
        :param data: Dict
        :return: None
        """
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'wb') as f:
            yaml.dump(data, stream=f, default_flow_style=False)

    @staticmethod
    def load_from_bag(filename):
        """
        Load yaml data from DEFAULT_TOPIC from rosbag into OrderedDict

        :param filename: Path to rosbag
        :return: OrderedDict with key value pairs from file or None upon file error
        """
        click.echo("Gathering metadata from bag {} ...".format(filename))
        try:
            with rosbag.Bag(filename, 'r') as bag:
                for msg_topic, msg, t in bag.read_messages(topics=[DEFAULT_TOPIC, ]):
                    if msg_topic == DEFAULT_TOPIC:
                        return ordered_load(msg.data)
                else:
                    return OrderedDict()
        except rosbag.bag.ROSBagException as err:
            click.secho(err.value, fg="red")
            return None

    def write_to_bag(self, bagfile):
        """
        Write Dictionary of metadata to rosbags DEFAULT_TOPIC

        Catches errors and prints warning
        :param filename: Path to rosbag
        :param data: dict
        :return: None
        """
        metadata = self.data
        if isinstance(metadata, dict):  # convert dict to yaml
            metadata = yaml.dump(metadata, default_flow_style=False)

        while os.path.exists(bagfile + ".active"):
            click.echo("Waiting for bagfile to be written to disk...")
            time.sleep(1)

        success = False
        try:
            with rosbag.Bag(bagfile, 'a') as bag:
                metadata_msg = std_msgs.msg.String(data=metadata)

                t = None
                for _, _, t in bag.read_messages():
                    break
                if t:
                    success = True
                    bag.write(DEFAULT_TOPIC, metadata_msg, t - rospy.rostime.Duration(0, 1))
        except rosbag.bag.ROSBagException as err:
            click.secho("Could not write to bagfile: {}".format(err.value), fg="red")

        if success:
            click.echo("\nWrote the following metadata to {}:".format(bagfile))
            click.echo(self.__str__())

    def collect_metadata(self, filename=METADATA_CACHE, clean_start=False):
        """
        Creates new metadata stub from template and updates it from data found in filename.
        Afterwards it will prompt the user to confirm entries and to add additional ones.
        :param filename: Path to file or rosbag with existing data
        :param clean_start: Do not use old data
        :return: None, data is stored in member variable
        """
        new_data = self.load_from_file(METADATA_TEMPLATE)
        if not clean_start:
            last_data = OrderedDict()
            if os.path.isfile(filename):
                if filename.endswith(".bag"):
                    last_data = self.load_from_bag(filename)
                    # Keep all of the old data
                    new_data.update(last_data)
                else:
                    last_data = self.load_from_file(filename)
            try:
                if str(last_data["General"]["MetaDataVers"]) != str(new_data["General"]["MetaDataVers"]):
                    click.secho("Wrong Version Number detected, dropping old data.", fg="yellow")
                    last_data = OrderedDict()
            except KeyError:
                pass

            if last_data:
                new_data = self.update_data(new_data, last_data)

        new_data = self.query_user(new_data, "Please provide information about this rosbag.")

        try:
            click.echo("Add additional fields now or continue by pressing Ctrl+d")
            while True:
                k = unidecode(click.prompt('Field name', type=click.STRING))
                v = unidecode(click.prompt(k, type=click.STRING))
                if "Custom" not in new_data:
                    new_data["Custom"] = OrderedDict()
                new_data["Custom"][k] = v
        except click.Abort:
            click.echo("")

        self.data = new_data
        self.write_to_file(METADATA_CACHE, new_data)

    def query_user(self, data, category):
        """
        For every entry in dict, prompt user to accept default value or specify custom input.
        :param data: Dictionary
        :param category: Name to print to console before prompts.
        :return: Filled Dictionary
        """
        click.echo("\n==" + str(category) + "==")
        for k, v in data.iteritems():
            if type(v) is OrderedDict:
                # If dict contains nested dicts -> recurse
                data[k] = self.query_user(data[k], k)
                continue
            elif k == "LastModified":
                # Wo know this, do not ask user
                data[k] = time.asctime()
                continue
            elif k == "MetaDataVersion":
                continue  # Use template version
            elif k == "CreatedBy":
                # Get user name as default value
                v = getpass.getuser()

            # We use the decode and unidecode functions to get rid of any non ascii signs, that could lead to trouble
            #  later on.
            data[k] = unidecode(click.prompt(k, default=str(v).decode("utf-8"), type=click.STRING))
        return data

    def update_data(self, data, default):
        """
        Copy data from old data into new data dict.
        Note: Only fields existing in the new dict are kept. Exception to this rule is the "custom" category.
        :param data: dict
        :param default: dict
        :return: dict
        """

        for k, v in data.iteritems():
            if k == "Custom" and "Custom" in default:
                data[k].update(default[k])
            elif type(v) is OrderedDict:
                data[k] = self.update_data(data[k], default[k])
            elif k in default:
                data[k] = default[k]
        return data
