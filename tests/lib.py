import pyblish.api


def clean():
    pyblish.api.deregister_all_paths()
    pyblish.api.deregister_all_plugins()
    pyblish.api.deregister_all_services()
