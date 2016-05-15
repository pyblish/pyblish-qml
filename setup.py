from setuptools import setup, find_packages


import os
import imp

version_file = os.path.abspath("pyblish_qml/version.py")
version_mod = imp.load_source("version", version_file)
version = version_mod.version


setup(
    name="pyblish-qml",
    version=version,
    long_description=readme,
    url="https://github.com/pyblish/pyblish",
    license="LGPL",
    packages=find_packages(),
    zip_safe=False,
    classifiers=classifiers
)
