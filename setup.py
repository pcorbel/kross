#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


# Get requirements
def get_requirements():
    with open("requirements.txt") as f:
        return f.read().splitlines()


def get_description():
    with open("README.md") as f:
        return f.read()


# Setup
setup(
    name="kross",
    version="1.0.2",
    license="apache-2.0",
    author="pcorbel",
    author_email="pierrot.corbel@gmail.com",
    url="https://github.com/pcorbel/kross",
    download_url="https://github.com/pcorbel/kross/archive/v1.0.2.tar.gz",
    description='A simple CLI to "multi-arch all the things"',
    long_description=get_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=get_requirements(),
    entry_points={"console_scripts": ["kross = kross.main:cli"]},
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
    ],
    include_package_data=True,
)
