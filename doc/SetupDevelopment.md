# Development Setup for the MRT tools
You cat setup the MRT tools in a virtual environment. This way, it won't conflict with your system wide installation and you can easily test your modifications to the code base.

## Requirements
Install the `virtualenvwrapper` for easier handling of virtual environments and other deps
```bash
sudo apt-get install virtualenvwrapper libffi-dev libkrb5-dev
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh # Can be put into bashrc
```

## Creating the virtualenv and installation
First, create a new virtual environment
```bash
mkvirtualenv mrt --system-site-packages
```
You will see a `(mrt)` at the beginning of your prompt, indicating that you are working in your virtualenv.
You can deactivate it with `deactivate`. To work in this environment again use the command `workon mrt`.

Setup the mrt_tools package
```bash
python setup.py install
```

You will now be able to use the development version, whenever your virtualenv is activated.
If you want to permanently use them, you can create a link to the executable and extend your path (the export command should go into your `.bashrc`):
```bash
mkdir -p  ~/.local/bin
ln -s ~/.virtualenvs/mrt/bin/mrt ~/.local/bin/mrt
export PATH=~/.local/bin:$PATH
```
## Updating
When you want to update your MRT tools, follow these steps in the build repo:
```bash
git pull
workon mrt
pip uninstall mrt
python setup.py install
```

## Deinstallation / start from scratch
Simply remove the virtual environment:
```bash
deactivate
rmvirtualenv mrt
```
