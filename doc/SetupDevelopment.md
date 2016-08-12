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
mkvirtualenv mrt
```
You will see a `(mrt)` at the beginning of your prompt, indicating that you are working in your virtualenv.
You can deactivate it with `deactivate`. To work in this environment again use the command `workon mrt`.

Now start by installing the required packages:
```bash
pip install -U -I -r requirements.txt
```
And setup the mrt_tools package as a link to the source code, so it is editable
```bash
python setup.py install
```

Finally, link some system packages into the virtualenv:
```bash
ln -s /usr/lib/python2.7/dist-packages/keyring $VIRTUAL_ENV/lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/gi $VIRTUAL_ENV/lib/python2.7/site-packages/
```

You will now be able to use the development version, whenever your virtualenv is activated.
If you want to permanently use them, you can create a link to the executable and extend your path (the export command should go into your `.bashrc`):
```bash
mkdirs ~/.local/bin
ln -s ~/.virtualenvs/mrt/bin/mrt ~/.local/bin/mrt
export PATH=~/.local/bin:$PATH
```

## Updating
When you want to update your MRT tools, follow these steps in the build repo:
```bash
git pull
workon mrt
pip uninstall mrt
pip install -U -I -r requirements.txt
python setup.py install
```

## Deinstallation / start from scratch
Simply remove the virtual environment:
```bash
deactivate
rmvirtualenv mrt
```
