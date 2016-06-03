#!/usr/bin/env python
# coding=utf-8

from setuptools import setup


# Use semantic versioning: MAJOR.MINOR.PATCH
version = '0.1.2'


def get_requires():
    try:
        with open('requirements.txt', 'r') as f:
            requires = [i for i in map(lambda x: x.strip(), f.readlines()) if i]
        return requires
    except IOError:
        return []


def get_long_description():
    try:
        with open('README.md', 'r') as f:
            return f.read()
    except IOError:
        return ''


setup(
    # license='License :: OSI Approved :: MIT License',
    name='deptest',
    version=version,
    author='reorx',
    author_email='novoreorx@gmail.com',
    description='dependent testing framework',
    url='https://github.com/reorx/deptest',
    long_description=get_long_description(),
    packages=[
        'deptest',
    ],
    # Or use (make sure find_packages is imported from setuptools):
    # packages=find_packages()
    # Or if it's a single file package
    # install_requires=get_requires(),
    # package_data={}
    entry_points={
        'console_scripts': [
            'deptest = deptest.core:main'
        ]
    }
)
