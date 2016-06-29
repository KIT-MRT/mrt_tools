# MRT Build Tools

The *MRT tools* are a collection of usefull command-line tools for developing, working with and distributing code at the MRT.  If there are any errors, please contact [Claudio](mailto:claudio.bandera@kit.edu) or have a look at [the Gitlab issue site](https://gitlab.mrt.uni-karlsruhe.de/MRT/mrt_build/issues).


## Installation

The *MRT tools* are automatically installed when the mrt_init script is executed. See the [install instructions](https://mrtwiki.mrt.uni-karlsruhe.de:10443/dokuwiki/doku.php?id=software:mrt_build_system:installation) for more infos.
If you have run the init script before and your apt-get repos are set up, you can install the *MRT tools* with:
```bash
    $ sudo apt-get install mrt-build-tools
```

### Development

If you'd like to work on a editable copy of the *MRT tools*, follow the instructions given [here](doc/SetupDevelopment.md)

## Getting Started

Using the *MRT tools* is as easy as typing:
```bash
    $ mrt
```

### Getting help

You can always get help by appending `--help` to any command, e.g.
```bash
$ mrt --help
Usage: mrt [OPTIONS] COMMAND [ARGS]...

    A toolbelt full of mrt scripts.

Options:
 1. -help  Show this message and exit.

Commands:
	catkin       A wrapper for catkin.
	gitlab       Gitlab related tools
	maintenance  Repair tools...
	pkg          Package related tasks...
	snapshot     Save or restore the current state of the...
	ws           A collection of tools to perform on a catkin...
	wstool       A wrapper for wstool.
```
### Example usage

#### Day 1:
First of, you want to get started by creating a new workspace. The toolset contains a bunch of tools to operate on workspaces you can get a list by typing `mrt ws --help`
```bash
    $ mkdir catkin_ws
    $ cd catkin_ws
    $ mrt ws init
```
or in short
```bash
    $ mrt ws init catkin_ws
```
This will initialize a new catkin workspace in the `catkin_ws` directory.

Next, you want to grab some existing software from the MRT-Gitlab. You can find a bunch of tools for working with (code-)packages via the `mrt pkg --help` command. Let's download the "calib_tool".
```bash
    $ mrt pkg add calib_tool
```
This will download and install all dependencies required for compiling the desired package.\\

**Hint:** Try using bash autocompletion on any of these command. For `mrt pkg add` it will present you with a list of all packages you have access to.

Now let's go ahead and compile the code. Therefor we are going to use `mrt catkin`, which adds a convenient wrapper around the `catkin` tools. This makes it inrelevant in which directory you are. Further more, you can pass special flags like `-rd`(resolve dependecies) or `--verbose` additional to the normal `catkin` flags to it.
```bash
    $ mrt catkin build
```

#### Day 2:

Welcome back, before we start of, let's see whether someone else might have worked on the code in the meanwhile. `cd` to your workspace and perform a
```bash
    $ mrt ws update
```
This will perform a `git pull` in every package within your workspaces "src" folder. This comes in handy, once you have a lot of repos in there.\\

**Hint:** There's also `mrt ws info` and `mrt ws status` to get information on any changed filed, or unpushed commits in your repos.

If you are looking for even more functionallity to operate on a large set on repositories, have a look at `mrt wstool` which is a wrapper for the `wstool` suite.

Let us create a new package now. Creating a new C++ catkin package called "your_package" can be done via
```bash
    $ mrt pkg create your_package
```
It will ask you whether to create a library or an executable, whether it should be a ROS package and whether you want to create a new Gitlab repository with it. You'll end up with a new package in your workspace's "src" folder, containing a sample "CMakeLists.txt", "package.xml" and a sample test. For more infos on these files, see [MRT cmake modules](https://mrtwiki.mrt.uni-karlsruhe.de:10443/dokuwiki/doku.php?id=software:mrt_build_system:mrt_cmake_modules).

#### Day 3:

Ok, now you have created a bunch of code, got it all up and running and want to perform a demonstration on one of the cars? Perfect!

Let me present to you the `mrt snapshot` functionality. With this you can easily capture the momentary state of your workspace and preserve it (hopefully) until eternity.
```bash
    $ mrt snapshot create the_big_demo
```
will create a "the_big_demo_[date].snapshot" file, which you can restore on any machine using:
```bash
    $ mrt snapshot restore "the_big_demo_[date].snapshot"
```

We are storing all snapshot files on "/mrtstorage/demo_snapshots".

#### Day X:

Now that you are used to the *MRT tools*, have a look at all the other commands, e.g.
```bash
    $ mrt gitlab ...
    $ mrt maintenance ...
```


## Configuration

After installation, *MRT tools* are configured with the default settings. These are for example:

*  "https" is used instead of "ssh"

*  Git credentials are cached for 1 hour.

*  Default ssh path...
You can change these and other settings by using
```bash
    $ mrt maintenance settings
```

## Further reading

*  ROS catkin: [http://docs.ros.org/api/catkin/html/Catkin](http://docs.ros.org/api/catkin/html/Catkin)

*  ROS dep: [http://docs.ros.org/independent/api/rosdep/html/](http://docs.ros.org/independent/api/rosdep/html/)

*  wstool: [http://wiki.ros.org/wstool](http://wiki.ros.org/wstool)

*  rosinstall: [http://docs.ros.org/independent/api/rosinstall/html/](http://docs.ros.org/independent/api/rosinstall/html/)
