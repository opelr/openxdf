from distutils.core import setup

setup(
    name="OpenXDF",
    version="0.4.0",
    author="Ryan Opel",
    author_email="ryan.a.opel@gmail.com",
    url="https://github.com/opelr/openxdf",
    packages=["openxdf"],
    license="LICENSE",
    description="OpenXDF is a Python module built for interacting with Open eXchange Data Format files.",
    long_description=open("README.md").read(),
    install_requires=["pandas >= 0.23.0", "xmltodict == 0.11.0"],
)
