# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='pyeia',
    version='0.0.2',

    description='Python client for Energy Information Administration (EIA) API',
    long_description='',

    url='https://github.com/thomastu/pyEIA',

    author='Thomas Tu',
    author_email='thomasthetu@gmail.com',

    license='BSD',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Researchers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='eia energy',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['future',
        'requests',
        'requests_cache',
        'pandas'],

    extras_require={
        'dev': ['check-manifest',],
        'test': ['coverage', 'nose'],
    },

    package_data={
    },

    entry_points={
    },
)
