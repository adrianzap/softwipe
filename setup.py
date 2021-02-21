"""
Test setup
"""

from setuptools import setup

setup(
    name='SoftWipe',
    version='0.2',
    packages=[''],
    package_data={'': ['KWStyle.xml']},
    include_package_data=True,
    long_description=open('README.md').read(),
    py_modules=["softwipe"],
    entry_points={
        'console_scripts': [
            'softwipe = softwipe:main',
        ],
    }
)
