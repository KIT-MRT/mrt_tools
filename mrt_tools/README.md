# MRT tools
The mrt tools, are a collection of scripts and programs to make software development in your everyday life easier.

It provides tools for:

 * handling and creating big workspaces full of git repos
 * creating new catkin packages
 * visualising and resolving dependencies

At the core of the mrt build tools, lies the idea of a unified build system. The system of our choice is **cmake**.
 We combine cmake with a powerfull wrapper for workspace handling and compiling. **catkin**.
The version control system (VCS) of our choice is **git**, with the graphical webinterface provided by **gitlab**.

Apart from these major components, some smaller tools are used to bring these tools together. Namely **wstool** for
handling huge workspaces full of git repositories and **rosdep** for handling dependency management and interaction
with the OS package management, **apt-get**.

Finally, **mrt tools** wrap all of these things up and automate many common workflows.


## MRT build reference

### Installation
Setup is as simple as:
1. Connect to the mrt VPN
2. Run the init script to install all prerequisits.
```bash
  $ /mrt/staff/wiss/repositories/mrt_build/mrt_init.run
```
3. Run ```mrt --help``` to get help. Btw: You can run any command with the ```--help``` flag, to get information
about the function call. Also, you can always use [TAB] to use autocompletion. Example help output:
```
    Usage: mrt [OPTIONS] COMMAND [ARGS]...

      A toolbelt full of mrt scripts.

    Options:
      --help  Show this message and exit.

    Commands:
      catkin          A wrapper for catkin.
      clone_pkg       Clone catkin packages from gitlab.
      create_pkg      Create a new catkin package
      init_workspace  Initialize a catkin workspace.
      resolve_deps    Resolve all dependencies in this workspace.
      snapshot
      visualize_deps  Visualize dependencies of catkin packages.
      wstool          A wrapper for wstool.
```


### Setting up a new workspace

To set up a new workspace, in which to work on code, simply run:
```bash
  $ mrt init_workspace
```
This will create a new mrt workspace by initialising catkin and wstool. Run this script in the place you would like
to create your workspace. The folder should be empty.

### Getting code

Once you have set up your catkin workspace, work becomes easy. Clone any repository from the MRT Gitlab server into
your workspace, by running
```bash
  $ mrt clone_pkg PKG_NAME
```
Where PKG_NAME is one of the gitlab repositories. (In a future release, we'll have bash completion in order to give
you suggestions on which repos exist.)

This command will automatically resolve dependencies and install every other required library or apt package. See
next section for more infos.

### Resolving dependencies

One huge problem, when working with someone elses code are dependencies to other libraries. This often gets you
caught up in a x hour marathon to track down and install all dependencies. The mrt build tool, assist you in this
task, by automatically resolving all dependencies from your packages.

These dependencies can either be other repositories, or rosdep dependencies (apt-get packages). If you ever find that
 your projects has external dependencies, that are not available through apt-get yet, see **mrt cmake-modules** for
 creating you own debian packages.

Dependencies are always resolved when cloning new packages. But you can also trigger it manually via:
```bash
  $ mrt resolve_deps
```
Or while compiling:
```bash
  $ mrt catkin build -rd
```

Please be aware, that dependencies have to be declared within the ```package.xml``` file. See "Creating new packages"
 for more infos.

### Visualizing dependencies

#### For single packages
Every now and then you find yourself surprised to see that your package requires a vast amount of other packages. To
assist you in understanding these connections, you can use
```bash
  $ mrt visualize_deps PKG_NAME
```
This will create a full-depth graph of this packages dependency graph. The images will be stored in
```<workspace root>/pics/```. Green nodes symbolize gitlab repos, red nodes symbolize external dependencies.

#### For the whole workspace
When invoked without arguments, **mrt visualize_deps** can create dependency graphs for every single package within
the workspace and/or one overall graph off all packages.


### Compiling code
The MRT tools rely on a common build system. The system of choice is cmake, combined with
[catkin](https://catkin-tools.readthedocs.org/en/latest/) as a powerful wrapper. When you use the mrt tools, you
have to use cmake. Even though this might mean some more work at the beginning, it gives you lots of benefits in the
long run. See "Creating new packages" for more infos.

To compile code in your workspace, use
```bash
  $ mrt catkin build
```



//Build the current workspace.//
This script is a light wrapper around [[https://catkin-tools.readthedocs.org/en/latest/|catkin]] to solve repetitive tasks.
=== Usage ===
<code bash>mrt_catkin [-option] <command></code>
=== Arguments ===
The additional ''option'' flags, which are handled by mrt_catkin are:
  * **%%--%%eclipse** -- Builds a eclipse project file, which can be imported into Eclipse
  * **%%--%%debug** -- Build in debug mode
  * **%%--%%release** -- Build in release mode
  * **%%--%%resolve-deps** -- Release and install all missing dependencies for the given workspace before building.
  * **-rd** -- Equivalent to %%--%%resolve-deps

The ''commands'' are passed to and handled by [[https://catkin-tools.readthedocs.org/en/latest/|catkin]]. Here are some examples:
  * **build** -- Build packages in a catkin workspace
  * **config** -- Configure a catkin workspace’s layout and settings
  * **clean** -- Clean products generated in a catkin workspace
  * **create** -- Create structrures like Catkin packages
  * **init** -- Initialize a catkin workspace
  * **list** -- Find and list information about catkin packages in a workspace
  * **profile** -- Manage different named configuration profiles
=== Additional Infos ===
If you would like to use eclipse, you have to do install and configure eclipse to get the indexing with c++14 right. See [[wissenswertes:ubuntu:eclipse_einrichten|Setup eclipse]] for further instructions.

----
### Creating own software
===== mrt_create_pkg =====
//Creates a new package in the current workspace.// \\
Sets up the correct directory structure and creates required files for cmake and dependency management. Optionally it can also set up a new gitlab repository.
=== Usage ===
<code bash>mrt_create_pkg [options] <name></code>
=== Arguments ===
If you do not specify any parameters then the script is run in interactive mode.

The following options can be passed
  * **-h** -- Display help
  * **-t** -- [//lib/////exec//] Specifies the type, can be library or executable
  * **-r** -- (optional) Create ROS Package
  * **-g** -- (optional) Create GitLab repository

**<name>** defines the name for the new Package.
### Recording the state of a workspace
### Handling workspaces
//Manages git repositories.// \\
This script is a light wrapper around wstool to solve repetitive tasks.
=== Usage ===
<code bash>mrt_wstool <command></code>
=== Arguments ===
  * **help** -- provide help for commands
  * **init** -- set up a directory as workspace
  * **set** -- add or changes one entry from your workspace config
  * **merge** -- merges your workspace with another config set
  * **remove** -- remove an entry from your workspace config, without deleting files
  * **update** -- updates info an existing repositories, checks for unpushed commits and performs a git pull on each repo.
  * **update push** -- Same as above, but wont ask before pushing
  * **info** -- Overview of some entries
  * **status** -- print the change status of files in some SCM controlled entries
  * **diff** -- print a diff over some SCM controlled entries
=== Additional Infos ===
Repository info is stored in ''src/.rosinstall''



### Further reading
  * ROS catkin: http://docs.ros.org/api/catkin/html/Catkin
  * ROS dep: http://docs.ros.org/independent/api/rosdep/html/
  * wstool: http://wiki.ros.org/wstool
  * rosinstall: http://docs.ros.org/independent/api/rosinstall/html/

