import setuptools
from distutils.core import setup
from openxdf import (
    __title__,
    __version__,
    __author__,
    __author_email__,
    __description__,
    __url__
)

setup(
    name=__title__,
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=open("README.md").read(),
    url=__url__,
    packages=setuptools.find_packages(),
    install_requires=["xmltodict", "pandas"],
    license=open("LICENSE").read(),
    entry_points={"console_scripts": ["pretty_xdf=openxdf.pretty:main"]},
)
