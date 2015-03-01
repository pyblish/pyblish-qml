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
    for suffix in ("ttf", "qml", "js", "txt", "png"):
        relpath = os.path.relpath(root, qml_dir)
        relpath = relpath.replace("\\", "/")
        qml_package_data.append("qml/" + relpath.strip(".") + "/*." + suffix)


classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities"
]

setup(
    name="pyblish-qml",
    version=version,
    description="Frontend for Pyblish",
    long_description=readme,
    author="Abstract Factory and Contributors",
    author_email="marcus@abstractfactory.com",
    url="https://github.com/pyblish/pyblish-qml",
    license="LGPL",
    packages=find_packages(),
    zip_safe=False,
    classifiers=classifiers,
    package_data={
        "pyblish_qml": qml_package_data
    },
    entry_points={},
    install_requires=["pyblish-endpoint>=1.1.3",
                      "pyblish>=1.0.12"]
)
