#!/usr/bin/env python

"""
Setup script
"""

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
        raise RuntimeError('No version set in nuancier/__init__.py')
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
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
)
