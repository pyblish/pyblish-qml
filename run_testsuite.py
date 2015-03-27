import os
import sys

# Expose vendor packages to PYTHONPATH
repo_dir = os.path.dirname(__file__)
package_dir = os.path.join(repo_dir, "pyblish_qml")
vendor_dir = os.path.join(package_dir, "vendor")
sys.path.insert(0, vendor_dir)

import nose


if __name__ == '__main__':
    argv = sys.argv[:]
    argv.extend(['--exclude=vendor', '--with-doctest'])
    nose.main(argv=argv)
