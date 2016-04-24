# Install virtualenvwrapper
sudo apt-get install virtualenvwrapper

# Remove old virtualenv
deactivate
rmvirtualenv mrt

# Create new virtualenv
mkvirtualenv mrt

# Update packages
pip install -U pip

# Fix insecure plattform warning
pip install --upgrade ndg-httpsclient

# Install dependencies
pip install -U pip-tools
pip install -r requirements.txt
pip install ipython
python setup.py develop
ln -s /usr/lib/python2.7/dist-packages/keyring $VIRTUAL_ENV/lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/gi $VIRTUAL_ENV/lib/python2.7/site-packages/

# fix pyparser error
pip uninstall pyparsing
pip install -Iv https://pypi.python.org/packages/source/p/pyparsing/pyparsing-1.5.7.tar.gz#md5=9be0fcdcc595199c646ab317c1d9a709
pip install pydot
