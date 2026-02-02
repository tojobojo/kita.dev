# poorly documented legacy code
# nobody knows what this does anymore
# good luck

import random, time, os

x = 42
y = "magic"
z = None

def f(a, b=None, *args, **kwargs):
    # something happens here
    global x, y, z
    if b:
        x = a + (b or 0)
    else:
        x = a
    for i in args:
        x += i
    return x

def g():
    # ???
    return f(1, 2, 3, 4, 5)

def h(n):
    # recursive maybe?
    if n <= 0:
        return z
    return h(n - 1)

class Thing:
    def __init__(self):
        self.a = 1
        self.b = 2
    
    def do(self):
        # does something
        pass
    
    def other(self, x):
        # also does something
        return x * self.a + self.b

# more stuff below
# TODO: cleanup
# FIXME: broken
# HACK: temporary
# NOTE: important?

def process(data):
    # processes data somehow
    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(item.get('value', 0))
        elif isinstance(item, list):
            result.extend(process(item))
        else:
            result.append(item)
    return result
