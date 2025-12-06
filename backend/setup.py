#!/usr/bin/env python
"""Setup script for PhotoSafe CLI"""

from setuptools import setup, find_packages

setup(
    name="photosafe-cli",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0",
        "fastapi>=0.115.5",
        "sqlalchemy>=2.0.36",
        "boto3>=1.34.0",
    ],
    entry_points={
        "console_scripts": [
            "photosafe=cli.main:cli",
        ],
    },
)
