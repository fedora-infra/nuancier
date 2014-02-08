#!/usr/bin/env python

"""
Setup script
"""

# Required to build on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import os
import shutil


if os.path.exists('nuancier/static/pictures'):
    shutil.rmtree('nuancier/static/pictures')
if os.path.exists('nuancier/static/cache'):
    shutil.rmtree('nuancier/static/cache')


from setuptools import setup
from nuancier import __version__


setup(
    name='nuancier',
    description='A voting application for the supplementary wallpapers of '
                'Fedora',
    version=__version__,
    author='Pierre-Yves Chibon',
    author_email='pingou@pingoured.fr',
    maintainer='Pierre-Yves Chibon',
    maintainer_email='pingou@pingoured.fr',
    license='GPLv2+',
    download_url='https://fedorahosted.org/releases/n/u/nuancier/',
    url='https://github.com/fedora-infra/nuancier/',
    packages=['nuancier'],
    include_package_data=True,
    install_requires=['Flask', 'SQLAlchemy>=0.6', 'wtforms', 'flask-wtf',
                      'python-fedora', 'Pillow', 'dogpile.cache', 'blinker'],
)
