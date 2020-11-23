"""
Test setup
"""
from setuptools import setup, find_packages

setup(
    name='SoftWipe',
    version='0.1',
    packages=['softwipe',],
    package_data={'softwipe': ['KWStyle.xml']},
    include_package_data=True,
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': [
            'softwipe = softwipe.softwipe:main',
        ],
    }
)