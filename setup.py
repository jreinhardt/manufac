from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Get the version from the relevant file
with open(path.join(here, 'version'), encoding='utf-8') as f:
    version = f.read().strip()

setup(
    name='manuallabour-cl',
    version=version,
    packages=find_packages(exclude=['tests','docs']),
    namespace_packages=['manuallabour'],
    description='Commandline interface for Manual Labour',
    long_description=long_description,
    install_requires = ['manuallabour','jsonschema','pyyaml'],
    entry_points={
        'console_scripts': ['manuallabour = manuallabour.cl:main_function']
    }
)