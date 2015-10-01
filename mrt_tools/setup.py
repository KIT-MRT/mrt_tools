"""
A toolbelt full of mrt scripts
"""
from setuptools import find_packages, setup

dependencies = ['click', 'pyapi-gitlab', 'wstool', 'catkin_pkg', 'pydot2', 'Image', 'pycrypto', 'future']

setup(
    name='mrt',
    version='2.0.0',
    url='https://github.com/cbandera/mrt_build',
    license='GPL-3.0+',
    author='Claudio Bandera',
    author_email='claudio.bandera@kit.edu',
    description='A toolbelt full of mrt scripts',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
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
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL-3.0+ License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
