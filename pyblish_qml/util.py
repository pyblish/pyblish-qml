import re
import time
import types
import traceback

from functools import wraps
from PyQt5 import QtCore

from .vendor import six

_timers = {}
_async_threads = []
_data = {
    "dispatch_wrapper": None
}
_jobs = dict()


class QState(QtCore.QState):
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def __init__(self, name, *args, **kwargs):
        super(QState, self).__init__(*args, **kwargs)
        self.name = name
        self.setObjectName(name)

        # machine.configuration() throws an exception
        # under Python 3 unless this useless variable
        # is set? In Python 2 however, setting this
        # variable causes a segfault.
        if six.PY3:
            self.QState = None


class ItemList(list):
    """List with keys

    Raises:
        KeyError is item is not in list

    Example:
        >>> Obj = type("Object", (object,), {})
        >>> obj = Obj()
        >>> obj.name = "Test"
        >>> l = ItemList(key="name")
        >>> l.append(obj)
        >>> l[0] == obj
        True
        >>> l["Test"] == obj
        True
        >>> try:
        ...   l["NotInList"]
        ... except KeyError:
        ...   print(True)
        True

    """

    def __init__(self, key):
        self.key = key

    def __getitem__(self, index):
        if isinstance(index, int):
            return super(ItemList, self).__getitem__(index)

        for item in self:
            if getattr(item, self.key) == index:
                return item

        raise KeyError("%s not in list" % index)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default


def echo(text=""):
    print(text)


def timer(name):
    if name in _timers:
        return
    _timers[name] = time.time()


def timer_end(name, format=None):
    _time = _timers.pop(name, None)
    format = format or name + ": %.3f ms"
    if _time is not None:
        ms = (time.time() - _time) * 1000
        echo(format % ms)


def chain(*operations):
    """Run callables one after the other

    The output of the last callable is passed to the next.

    Arguments:
        operations (list): Callables to run

    Returns:
        Result from last operation

    """

    result = None
    for operation in operations:
        result = operation(result)

    return result


def async(target, args=None, kwargs=None, callback=None):
    """Perform operation in thread with callback

    Instances are cached until finished, at which point
    they are garbage collected. If we didn't do this,
    Python would step in and garbage collect the thread
    before having had time to finish, resulting in an
    exception.

    Arguments:
        target (callable): Method or function to call
        callback (callable, optional): Method or function to call
            once `target` has finished.

    Returns:
        None

    """

    obj = _Async(target, args, kwargs, callback)
    obj.finished.connect(lambda: _async_cleanup(obj))
    obj.start()
    _async_threads.append(obj)
    return obj


class _Async(QtCore.QThread):

    done = QtCore.pyqtSignal(QtCore.QVariant, arguments=["result"])

    def __init__(self, target, args=None, kwargs=None, callback=None):
        super(_Async, self).__init__()

        self.args = args or list()
        self.kwargs = kwargs or dict()
        self.target = target
        self.callback = callback

        if callback:
            connection = QtCore.Qt.BlockingQueuedConnection
            self.done.connect(self.callback, type=connection)

    def run(self, *args, **kwargs):
        try:
            result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            return self.done.emit(e)
        else:
            self.done.emit(result)


def _async_cleanup(obj):
    _async_threads.remove(obj)


def schedule(func, time, channel="default"):
    """Run `func` at a later `time` in a dedicated `channel`

    Given an arbitrary function, call this function after a given
    timeout. It will ensure that only one "job" is running within
    the given channel at any one time and cancel any currently
    running job if a new job is submitted before the timeout.

    """

    try:
        _jobs[channel].stop()
    except (AttributeError, KeyError):
        pass

    timer = QtCore.QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(func)
    timer.start(time)

    _jobs[channel] = timer


class Timer(object):
    """Time operations using this context manager

    Arguments:
        format (str): Optional format for output. Defaults to "%.3f ms"

    """

    def __init__(self, format=None):
        self._format = format or "%.3f ms"

    def __enter__(self):
        self._time = time.time()

    def __exit__(self, type, value, tb):
        print(self._format % ((time.time() - self._time) * 1000))


def format_text(text):
    """Remove newlines, but preserve paragraphs"""
    result = ""
    for paragraph in text.split("\n\n"):
        result += " ".join(paragraph.split()) + "\n\n"

    result = result.rstrip("\n")  # Remove last newlines

    # converting links to HTML
    pattern = r"(https?:\/\/(?:w{1,3}.)?[^\s]*?(?:\.[a-z]+)+)"
    pattern += r"(?![^<]*?(?:<\/\w+>|\/?>))"
    if re.search(pattern, result):
        html = r"<a href='\1'><font color='FF00CC'>\1</font></a>"
        result = re.sub(pattern, html, result)

    return result


def pyqtConstantProperty(fget):
    return QtCore.pyqtProperty(QtCore.QVariant,
                               fget=fget,
                               constant=True)


def SlotSentinel(*args):
    """Provides exception handling for all slots"""

    # (NOTE) davidlatwe
    # Thanks to this answer
    # https://stackoverflow.com/questions/18740884

    if len(args) == 0 or isinstance(args[0], types.FunctionType):
        args = []

    @QtCore.pyqtSlot(*args)
    def slotdecorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args)
            except Exception:
                traceback.print_exc()
        return wrapper

    return slotdecorator
