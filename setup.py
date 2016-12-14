#!/usr/bin/env python

"""
Setup script
"""

# Required to build on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']  # NOQA
import pkg_resources  # NOQA

from setuptools import setup
import os
import re
import shutil


if os.path.exists('nuancier/static/pictures'):
    shutil.rmtree('nuancier/static/pictures')
if os.path.exists('nuancier/static/cache'):
    shutil.rmtree('nuancier/static/cache')


def get_version():
    """Get the current version of the hotness package"""
    with open('nuancier/__init__.py', 'r') as fd:
        regex = r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]'
        version = re.search(regex, fd.read(), re.MULTILINE).group(1)
    if not version:
        raise RuntimeError('No version set in hotness/__init__.py')
    return version


def get_requirements(requirements_file='requirements.txt'):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    lines = open(requirements_file).readlines()
    return [
        line.rstrip().split('#')[0]
        for line in lines
        if not line.startswith('#')
    ]


setup(
    name='nuancier',
    description='A voting application for the supplementary wallpapers of '
                'Fedora',
    version=get_version(),
    author='Pierre-Yves Chibon',
    author_email='pingou@pingoured.fr',
    maintainer='Pierre-Yves Chibon',
    maintainer_email='pingou@pingoured.fr',
    license='GPLv2+',
    download_url='https://fedorahosted.org/releases/n/u/nuancier/',
    url='https://github.com/fedora-infra/nuancier/',
    packages=['nuancier'],
    include_package_data=True,
    install_requires=get_requirements(),
    tests_require=get_requirements('test-requirements.txt'),
)
