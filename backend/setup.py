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
        "requests>=2.31",
        "python-dateutil>=2.8.0",
        "tqdm>=4.66",
        "Pillow>=11.0",
        "pytz>=2024.1",
    ],
    extras_require={
        "macos": [
            "osxphotos>=0.60",
        ],
        "icloud": [
            "pyicloud",
        ],
    },
    entry_points={
        "console_scripts": [
            "photosafe=cli.main:cli",
        ],
    },
)
