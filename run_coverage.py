import sys

if __name__ == "__main__":
    import nose
    argv = sys.argv[:]
    argv.extend(["-c", ".noserc"])
    nose.main(argv=argv)
