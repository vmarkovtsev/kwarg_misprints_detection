"""
Detection of misprinted and unhandled function keyword argument names.

detect_misprints(fn) is the corresponding function decorator;
KeywordArgsMisprintsDetector is the metaclass to analyze class' __init__().

Copyright (c) 2015 Samsung Electronics Co., Ltd.
Copyright (c) 2015 Vadim Markovtsev.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the Samsung Electronics Co., Ltd. nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

try:
    from dis import get_instructions
    USE_DIS = True
except ImportError:
    # Unavailable in CPython < 3.4
    import re
    USE_DIS = False
import inspect
from pyxdameraulevenshtein import damerau_levenshtein_distance
import warnings


def get_kwarg_names(fn):
    """ Returns a set of the real names behind **kwargs.
    """
    kwarg_names = set()
    try:
        arg_spec = inspect.getargspec(fn)
    except TypeError:
        return kwarg_names
    kw_var = arg_spec.keywords
    if kw_var is None:
        return kwarg_names

    # Add names of arguments which have a default value
    if arg_spec.defaults is not None and len(arg_spec.defaults) > 0:
        kwarg_names.update(arg_spec.args[-len(arg_spec.defaults):])
    if USE_DIS:
        try:
            instrs = get_instructions(fn)
        except TypeError:
            return kwarg_names
        loading_fast_kwargs = False
        for inst in instrs:
            # https://hg.python.org/cpython/file/b3f0d7f50544/Include/opcode.h  # nopep8
            # 124 = LOAD_FAST
            # 106 = LOAD_ATTR
            # 100 = LOAD_CONST
            if inst.opcode == 124 and inst.argval == kw_var:
                loading_fast_kwargs = True
            elif loading_fast_kwargs and inst.opcode == 106:
                continue
            elif loading_fast_kwargs and inst.opcode == 100:
                kwarg_names.add(inst.argval)
                loading_fast_kwargs = False
            else:
                loading_fast_kwargs = False
    else:
        try:
            src, _ = inspect.getsourcelines(fn)
        except TypeError:
            return kwarg_names
        kwarg_re = re.compile(
            r"%(kwargs)s\.get\(([^\s,\)]+)|%(kwargs)s\[([^\]]+)" %
            {"kwargs": kw_var})
        for line in src:
            match = kwarg_re.search(line)
            if match is not None:
                kwarg_names.add((match.group(1) or match.group(2))[1:-1])

    return kwarg_names


def check_misprints(kwarg_names, given_kwarg_names, tolerance=1,
                    warn=warnings.warn):
    """ Warns about unhandled keyword arguments.
    """
    # Build the matrix of differences
    matrix = {}
    matched = set()
    for given_kwarg in given_kwarg_names:
        for kwattr in kwarg_names:
            if (kwattr, given_kwarg) in matrix:
                continue
            matrix[(given_kwarg, kwattr)] = d = \
                damerau_levenshtein_distance(given_kwarg, kwattr)
            if d == 0:
                # perfect match, stop further comparisons
                matched.add(given_kwarg)
                break
    if len(matched) < len(given_kwarg_names):
        # Find replacement candidates with distance = 1
        ignored_kwargs = []
        for given_kwarg in set(given_kwarg_names) - matched:
            candidates = []
            for kwattr in kwarg_names:
                d = matrix.get((given_kwarg, kwattr))
                if 0 < d <= tolerance:
                    candidates.append(kwattr)
            if len(candidates) == 0:
                ignored_kwargs.append(given_kwarg)
            else:
                warn("potential misprint in keyword argument "
                     "name: expected %s - got %s" %
                     (" or ".join(sorted(candidates)), given_kwarg))
        if len(ignored_kwargs) > 0:
            warn("ignored the following keyword arguments: %s" %
                 ", ".join(sorted(ignored_kwargs)))


def detect_misprints(fn):
    """ Function decorator which warns about unused keyword argumentimport s.
    """
    kwarg_names = get_kwarg_names(fn)
    if len(kwarg_names) == 0:
        return kwarg_names

    def warn(msg):
        warnings.warn("Calling %s(): %s" % (fn.__name__, msg))

    def wrapped(*args, **kwargs):
        check_misprints(kwarg_names, kwargs, warn=warn)
        return fn(*args, **kwargs)

    wrapped.__name__ = "detect_misprints_" + fn.__name__
    return wrapped


class KeywordArgsMisprintsDetector(type):
    def __init__(cls, name, bases, clsdict):
        kwarg_names = set()
        for base in cls.__mro__:
            kwarg_names.update(get_kwarg_names(base.__init__))
        cls.KWARG_NAMES = kwarg_names
        super(KeywordArgsMisprintsDetector, cls).__init__(name, bases, clsdict)

    def __call__(cls, *args, **kwargs):
        """ Checks for misprints in class' constructor keyword argument names
        """
        obj = super(KeywordArgsMisprintsDetector, cls).__call__(
            *args, **kwargs)

        def warn(msg):
            warnings.warn("Creating %s: %s" % (obj, msg))

        check_misprints(cls.KWARG_NAMES, kwargs, warn=warn)
        return obj
