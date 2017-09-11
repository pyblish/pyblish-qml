"""PyPI setup script

Script includes primary Python package along with essential
non-Python files, such as QML and .png resources.

Usage:
    >>> python setup.py sdist
    ...

"""

import os
import imp
from setuptools import setup, find_packages

with open("README.txt") as f:
    readme = f.read()

version_file = os.path.abspath("pyblish_qml/version.py")
version_mod = imp.load_source("version", version_file)
version = version_mod.version

# Collect non-python data as package data
qml_dir = os.path.abspath('pyblish_qml/qml')
qml_package_data = list()
for root, dirs, files in os.walk(qml_dir):
    for suffix in ("ttf", "qml", "js", "txt", "png", "py", "otf"):
        relpath = os.path.relpath(root, qml_dir)
        relpath = relpath.replace("\\", "/")
        qml_package_data.append("qml/" + relpath.strip(".") + "/*." + suffix)

# qmldir file has no suffix
qml_package_data.append(os.path.join("qml", "Pyblish", "qmldir"))
qml_package_data.append(os.path.join("qml", "Pyblish", "Graphs", "qmldir"))
qml_package_data.append(os.path.join("qml", "Pyblish", "ListItems", "qmldir"))
qml_package_data.append(os.path.join("qml", "Perspective", "qmldir"))

# icon file is in root dir
qml_package_data.append("icon.ico")
qml_package_data.append("splash.png")

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.1",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities"
]

setup(
    name="pyblish-qml",
    version=version,
    description="Frontend for Pyblish written in PyQt5/QML",
    long_description=readme,
    author="Abstract Factory and Contributors",
    author_email="marcus@abstractfactory.com",
    url="https://github.com/pyblish/pyblish-qml",
    license="LGPL",
    packages=find_packages(),
    zip_safe=False,
    classifiers=classifiers,
    package_data={
        "pyblish_qml": qml_package_data + [
            "vendor/jsonschema/schemas/*.json"
        ],
        "pyblish_qml.ipc": [
            "schema/*.json",
        ]
    },
    install_requires=[
        "pyblish-base==1.5.3"
    ],
    entry_points={},
)
