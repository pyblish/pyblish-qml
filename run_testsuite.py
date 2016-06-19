import sys


if __name__ == '__main__':
    import nose
    argv = sys.argv[:]
    argv.extend(['--exclude=vendor', '--with-doctest', "--verbose"])
    nose.main(argv=argv)
