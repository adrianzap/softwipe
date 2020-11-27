"""
Test setup
"""

from setuptools import setup, find_packages

setup(
    name='SoftWipe',
    version='0.1',
    packages=find_packages(),
    long_description=open('README.txt').read(),
    entry_points={
        'console_scripts': [
            'softwipe = softwipe:main',
        ],
    }
)