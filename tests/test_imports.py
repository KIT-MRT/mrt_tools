def test_click():
    import click

    try:
        @click.command()
        @click.argument("arg1", type=click.STRING, required=True, autocompletion=["foo", "bar"])
        def command_test(arg1):
            pass
    except TypeError as err:
        if err.message == "__init__() got an unexpected keyword argument 'autocompletion'":
            raise TypeError("Wrong version of click installed. Please install https://github.com/cbandera/click.git.")


def test_gnome_keyring():
    from Crypto.PublicKey import RSA
    import keyring
    keyring.set_keyring(keyring.backends.Gnome.Keyring())
    keyring.get_password("test", "test")


def test_base_imports():
    from builtins import next
    from builtins import object
    from builtins import str
    from collections import OrderedDict
    from os import chmod
    import ConfigParser
    import fcntl
    import fnmatch
    import getpass
    import grp
    import hashlib
    import os
    import paramiko
    import pwd
    import re
    import shutil
    import stat
    import subprocess
    import sys
    import tarfile
    import tempfile
    import termios
    import time
    import unidecode
    import webbrowser
    import xml.etree.ElementTree as ET
    import yaml
    import zipfile


def test_catkin():
    from catkin_pkg import packages
    from catkin_tools.context import Context


def test_wstool():
    import wstool


def test_gitlab():
    import gitlab
    from requests.exceptions import ConnectionError
    from requests.packages import urllib3
    from simplejson.scanner import JSONDecodeError


def test_pydot():
    import pydot


if __name__ == '__main__':
    test_click()
    test_gnome_keyring()
    test_base_imports()
    test_catkin()
    test_gitlab()
    test_pydot()
    test_wstool()
