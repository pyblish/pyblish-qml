import time

from pyblish_qml import util

import lib

# Vendor libraries
from nose.tools import (
    with_setup,
    assert_true,
    assert_equals
)


@with_setup(lib._setup)
def test_async():
    """util.async works as expected"""

    mutable = dict()

    def expensive_function():
        time.sleep(0.1)
        return 5

    def on_expensive_function(result):
        mutable["result"] = result
        lib.app.quit()

    qthread = util.async(expensive_function,
                         callback=on_expensive_function)

    lib.app.exec_()

    assert_true(qthread.wait(200))
    assert_equals(mutable["result"], 5)


def test_chain_with_functions():
    """util.chain works with functions"""
    def ten(data):
        return 10

    def mult_by_2(data):
        return data * 2.0

    def divide_by_4(data):
        return data / 4.0

    result = util.chain(ten, mult_by_2, divide_by_4)
    assert_equals(result, 5)


def test_chain_with_lambdas():
    """util.chain works with lambdas"""
    result = util.chain(lambda result: 5, lambda result: result * 2)
    assert_equals(result, 10)
