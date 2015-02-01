"""
DUnit tests for kwarg_misprints_detection.py.

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

from __future__ import print_function
from kwarg_misprints_detection import (detect_misprints,
                                       KeywordArgsMisprintsDetector)
from six import add_metaclass
import unittest
import warnings


class TestMisprintsDetection(unittest.TestCase):
    def setUp(self):
        self.warn_backup = warnings.warn
        warnings.warn = self.handleWarning
        self.warnings = []

    def tearDown(self):
        warnings.warn = self.warn_backup

    def handleWarning(self, msg):
        self.warnings.append(msg)
        print(msg)

    def checkWarning(self, part):
        self.assertTrue(any(part in w for w in self.warnings))

    def testDecorator(self):

        @detect_misprints
        def foo(arg1, arg2=1, **kwargs):
            kwa1 = kwargs["foo"]
            kwa2 = kwargs.get("bar", 200)
            kwa3 = kwargs.get("baz") or 3000
            return arg1 + arg2 + kwa1 + kwa2 + kwa3

        res = foo(0, arg3=100, foo=10, fo=2, bard=3, bas=4, oth=5, last=6)
        self.assertEqual(res, 0 + 1 + 10 + 200 + 3000)
        self.checkWarning("expected arg2 - got arg3")
        self.checkWarning("expected bar or baz - got bas")
        self.checkWarning("expected bar - got bard")
        self.checkWarning("expected foo - got fo")
        self.checkWarning("ignored the following keyword arguments: last, oth")
        self.assertEqual(len(self.warnings), 5)

    def testMetaclass(self):

        @add_metaclass(KeywordArgsMisprintsDetector)
        class Foo(object):
            def __init__(self, arg1, arg2=1, **kwargs):
                self.kwa0 = arg2
                self.kwa1 = kwargs["foo"]
                self.kwa2 = kwargs.get("bar", 200)
                self.kwa3 = kwargs.get("baz") or 3000

        class Bar(Foo):
            def __init__(self, arg1, arg2=1, **kwargs):
                super(Bar, self).__init__(arg1, arg2, **kwargs)
                self.kwa4 = kwargs.get("boo")

        self.assertEqual(Foo.KWARG_NAMES, {"arg2", "foo", "bar", "baz"})
        self.assertEqual(Bar.KWARG_NAMES, {"arg2", "foo", "bar", "baz", "boo"})

        foo = Foo(0, arg3=100, foo=10, fo=2, bard=3, bas=4, oth=5, last=6)
        self.assertEqual(foo.kwa0, 1)
        self.assertEqual(foo.kwa1, 10)
        self.assertEqual(foo.kwa2, 200)
        self.assertEqual(foo.kwa3, 3000)
        self.checkWarning("expected arg2 - got arg3")
        self.checkWarning("expected bar or baz - got bas")
        self.checkWarning("expected bar - got bard")
        self.checkWarning("expected foo - got fo")
        self.checkWarning("ignored the following keyword arguments: last, oth")
        self.assertEqual(len(self.warnings), 5)

        del self.warnings[:]
        del foo

        bar = Bar(0, arg3=100, foo=10, fo=2, bard=3, bas=4, oth=5, last=6,
                  bog=9)
        self.assertEqual(bar.kwa4, None)
        self.checkWarning("expected arg2 - got arg3")
        self.checkWarning("expected bar or baz - got bas")
        self.checkWarning("expected bar - got bard")
        self.checkWarning("expected foo - got fo")
        self.checkWarning("ignored the following keyword arguments: last, oth")
        self.checkWarning("expected boo - got bog")
        self.assertEqual(len(self.warnings), 6)

if __name__ == "__main__":
    unittest.main()
