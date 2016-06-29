# Development Setup for the MRT tools
You cat setup the MRT tools in a virtual environment. This way, it won't conflict with your system wide installation and you can easily test your modifications to the code base.

## Requirements
Install the `virtualenvwrapper` for easier handling of virtual environments
```bash
sudo apt-get install virtualenvwrapper
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh # Can be put into bashrc
```

## Creating the virtualenv and installation
First, create a new virtual environment
```bash
mkvirtualenv mrt
```
To work in this environment use the command `workon mrt`. You can deactivate it with `deactivate`.

Now start by installing the required packages:
```bash
pip install -U -I -r requirements.txt
```
And setup the mrt_tools package as a link to the source code, so it is editable
```bash
python setup.py develop
```

Finally, link some system packages into the virtualenv:
```bash
ln -s /usr/lib/python2.7/dist-packages/keyring $VIRTUAL_ENV/lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/gi $VIRTUAL_ENV/lib/python2.7/site-packages/
```

You will now be able to use the development version, whenever your virtualenv is activated. If you want to permanently use them, you can extend your path (can be put into your `.bashrc`):
```bash
export PATH=~/.virtualenvs/mrt/bin:$PATH
```

## Deinstallation / start from scratch
Simply remove the virtual environment:
```bash
deactivate
rmvirtualenv mrt
```
