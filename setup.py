"""
Test setup
"""

from setuptools import setup, find_packages

setup(
    name='SoftWipe',
    version='0.1',
    packages=[''],
    long_description=open('README.md').read(),
    py_modules=["softwipe"],
    entry_points={
        'console_scripts': [
            'softwipe = softwipe:main',
        ],
    }
)