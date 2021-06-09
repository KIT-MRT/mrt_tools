"""
A toolbelt full of mrt scripts
"""
import os
from setuptools import find_packages, setup

# Recursively gather data files to be installed
data_files = []
for root, dirnames, filenames in os.walk('mrt_tools/templates'):
    for filename in filenames:
        data_files.append(os.path.join(root[root.find('templates'):], filename))


setup(
    name='mrt',
    version='2.0.7',
    url='https://github.com/cbandera/mrt_build',
    license='GPL-3.0+',
    author='Claudio Bandera',
    author_email='claudio.bandera@kit.edu',
    description='A toolbelt full of mrt scripts',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    package_data={"mrt_tools": data_files},
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    dependency_links = [# Custom pip packages
                      'git+https://github.com/cbandera/click.git@8e18d48f925c312f47d2075e1392d49dc4818c95#egg=click',
                      'git+https://github.com/cbandera/pyapi-gitlab.git@057a1e4ec67037ba964f9531c236ee4737d3242a#egg=pyapi-gitlab',
                      # Fix dot parser error
                      'http://pypi.python.org/packages/source/p/pyparsing/pyparsing-1.5.7.tar.gz#md5=9be0fcdcc595199c646ab317c1d9a709',
                       ],
    install_requires=[# Python applications
                      'pip==19.2',
                      #'catkin-tools==0.4.2',
                      'wstool==0.1.12',
                      'pydot==1.1.0',
                      # Fix insecure plattform warning
                      'ndg-httpsclient==0.4.1',
                      # Pinning normal python packages
                      'argparse==1.4.0',
                      'catkin-pkg==0.2.10',
                      'click',
                      'ConfigParser==3.5.0',
                      'decorator==4.0.9',
                      'docutils==0.12',
                      'ecdsa==0.13',
                      'enum34==1.1.3',
                      'future==0.15.2',
                      'futures==3.0.5',
                      'python-gssapi==0.6.4',
                      'pyapi-gitlab',
                      'pyparsing',
                      'hashlib==20081119',
                      'osrf-pycommon==0.1.2',
                      'paramiko==1.16.0',
                      'pycrypto==2.6.1',
                      'python-dateutil==2.5.3',
                      'pyyaml==3.11',
                      'requests==2.9.1',
                      'rospkg==1.0.39',
                      'setuptools>=11.3',
                      'simplejson==3.8.2',
                      'six==1.10.0',
                      'trollius==2.1',
                      'idna==2.1',
                      'Unidecode==0.4.19',
                      'vcstools==0.1.38'
                      ],
    entry_points={
        'console_scripts': [
            'mrt = mrt_tools.cli:cli',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL-3.0+ License',
        # 'Operating System :: POSIX',
        # 'Operating System :: MacOS',
        'Operating System :: Unix',
        # 'Operating System :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)

