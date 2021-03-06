"""
Implementation of method '@synchronized' decorator.

it reflects functionality of 'synchronized' keyword from Java language.
It accepts one optional argument -- name of lock field declared within object.

Usage examples:

    @synchronized
    def send_dpg_write_command(self, dpgCommandType, data):
        pass

    @synchronized()
    def send_dpg_write_command(self, dpgCommandType, data):
        pass

    @synchronized("myLock")
    def send_dpg_write_command(self, dpgCommandType, data):
        pass

"""


import threading
from functools import wraps


def dirprint(var):
    names = dir(var)
    for name in names:
        if name == "__globals__":
            print( name, ": --globals--" )
        else:
            value = getattr(var, name)
            print( name, ":", value )


def extract_self(func, decorator, *args):
    params = args
    if len(params) < 1:
        return None
    ## 'self' goes always as first parameter
    firstParam = params[0]
    fName = func.__name__
    if hasattr(firstParam, fName) is False:
        return None
    ## object has method with the same name -- check if it has the same decorator
    method = getattr(firstParam, fName)
    if check_method(decorator, method):
        return firstParam
    return None


def check_method(func, method):
    if method.__func__ == func:
        return True
    return False


##
## Definition of function decorator
##
def synchronized_with_arg( lock_name=None ):
    if lock_name is None:
        lock_name = "_object_lock"

    def synced_method(func):
        ### every decorated method has it's own instance of 'decorator()' function
        @wraps(func)
        def decorator(self, *args, **kws):
#             owner = extract_self(func, decorator, *args)
#             if owner == None:
#                 return func(*args, **kws)
            lock = None
            if hasattr(self, lock_name) is False:
                lock = threading.RLock()
                setattr(self, lock_name, lock)
            else:
                lock = getattr(self, lock_name)
            with lock:
                return func(self, *args, **kws)
        return decorator

    return synced_method


def synchronized( lock_name=None ):
    if callable(lock_name):
        ### lock_name contains function to call
        function = lock_name
        synced = synchronized_with_arg()
        return synced(function)
    ### lock_name contains name of lock to handle
    synced = synchronized_with_arg(lock_name)
    return synced
