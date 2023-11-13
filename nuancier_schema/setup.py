#!/usr/bin/env python
#
# Copyright (C) 2019  Red Hat, Inc. and others.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
import os

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst")) as fd:
    README = fd.read()


setup(
    name="nuancier_schema",
    version="1.0.0",
    description="JSON schema definitions for messages published by Nuancier",
    long_description=README,
    url="https://github.com/fedora-infra/nuancier/",
    # Possible options are at https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    license="GPLv2+",
    maintainer="Fedora Infrastructure Team",
    maintainer_email="infrastructure@lists.fedoraproject.org",
    platforms=["Fedora", "GNU/Linux"],
    keywords="fedora",
    packages=find_packages(exclude=("anitya_schema.tests", "anitya_schema.tests.*")),
    include_package_data=True,
    zip_safe=False,
    install_requires=["fedora_messaging"],
    test_suite="nuancier_schema.tests",
    entry_points={
        "fedora.messages": [
            "nuancier.candidate.approved=nuancier_schema:CandidateApproved",
            "nuancier.candidate.denied=nuancier_schema:CandidateDenied",
            "nuancier.candidate.new=nuancier_schema:CandidateCreated",
            "nuancier.election.new=nuancier_schema:ElectionCreated",
            "nuancier.election.update=nuancier_schema:ElectionEdited",
        ]
    },
)
