import setuptools
from distutils.core import setup

setup(
    name="openxdf",
    version="0.4.0",
    author="Ryan Opel",
    author_email="ryan.a.opel@gmail.com",
    description="OpenXDF is a Python module built for interacting with Open eXchange Data Format files.",
    long_description=open("README.md").read(),
    url="https://github.com/opelr/openxdf",
    packages=setuptools.find_packages(),
    license="LICENSE",   
)
