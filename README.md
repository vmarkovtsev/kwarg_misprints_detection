# Python Function Keyword Argument Name Misprints Detection

Python allows passing to a function an unlimited number of keyword arguments through the double-starred last argument, like this:

```python
def foo(**kwargs):
    first = kwargs.get("first", ...)
    second = kwargs["second"]
    ...
```

Unfortunately, when the list of keyword arguments which are handled in this vay gets big, function user may pass in the wrong argument name by mistake, e.g.

```python
foo(second=2, fisrt=1)
```

Thus, such arguments get the default values and may lead to hard to debug errors. Another example is having a class which accepts `**kwargs` in it's constructor:

```python
class Foo(object):
    def __init__(self, **kwargs):
        first = kwargs.get("first", ...)
        ...

foo = Foo(frst=1)
```

This tiny package tries to warn about such typical errors. First it takes an attempt to find out what the actual keyword argument names are, either matching bytecode patterns in the output of `inspect.get_instructions()` on Python >3.4 or falling back to applying regular expressions on `inspect.getsourcelines()`. Then it builds the matrix of differences between those "real" names and the names which were actually passed in. The difference is calculated with [Damerau–Levenshtein distance](http://en.wikipedia.org/wiki/Damerau%E2%80%93Levenshtein_distance) algorithm and the excellent [pyxDamerauLevenshtein](https://github.com/gfairchild/pyxDamerauLevenshtein) library. Last, it warns about given args which are not similar to anything and similar to something.

### How to use

The described warner is available either as `detect_misprints` function decorator or `KeywordArgsMisprintsDetector` metaclass.

```python
from kwarg_misprints_detection import detect_misprints

@detect_misprints
def foo(**kwargs):
    first = kwargs.get("first", 2)
    return first  + 1

print(foo(fisrt=1))

UserWarning: Calling foo(): potential misprint in keyword argument name: expected first - got fisrt
3
```

The following assumes you have `six` package installed.

```python
from kwarg_misprints_detection import  KeywordArgsMisprintsDetector
from six import add_metaclass

@add_metaclass(KeywordArgsMisprintsDetector)
class Foo(object):
    def __init__(self, **kwargs):
        self.first = kwargs.get("first", 2)


print(Foo(irst=1).first)

Creating <__main__.Foo object at 0x10830fe80>: potential misprint in keyword argument name: expected first - got irst
2
```

This package supports both Python 2.7 and Python 3.x syntax. The code conforms to PEP8. Running tests requires `six`.

### License

New BSD License.

Copyright (c) 2015 Samsung Electronics Co., Ltd.

Copyright (c) 2015 Vadim Markovtsev.
