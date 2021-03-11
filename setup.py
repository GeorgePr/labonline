from distutils.core import setup

with open('requirements_dev.txt') as f:
    requirements = f.read().splitlines()

setup(
    name = 'LabOnLine',
    install_requires = requirements
)