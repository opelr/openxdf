from distutils.core import setup

setup(
    name='OpenXDF',
    version='0.1.0',
    author='Ryan Opel',
    author_email='ryan.a.opel@gmail.com',
    packages=['openxdf'],
    license='LICENSE',
    description='Processing exported Polysmith PSG files in OpenXDF format',
    long_description=open('README.md').read(),
    install_requires=[
        "pandas >= 0.23.0",
        "xmltodict == 0.11.0"
    ],
)