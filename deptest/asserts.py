# coding: utf-8
# flake8: noqa

"""Assert functions to make tests easier

these functions are exported from methods of unitest.TestCase class,
the original camel case name is converted to underscore style,
below is a complete list of function names compare to unittest method names:

almost_equal                  assertAlmostEqual
dict_contains_subset          assertDictContainsSubset
dict_equal                    assertDictEqual
equal                         assertEqual
false                         assertFalse
greater                       assertGreater
greater_equal                 assertGreaterEqual
in_                           assertIn
is_                           assertIs
is_instance                   assertIsInstance
is_none                       assertIsNone
is_not                        assertIsNot
is_not_none                   assertIsNotNone
items_equal                   assertItemsEqual
less                          assertLess
less_equal                    assertLessEqual
list_equal                    assertListEqual
multi_line_equal              assertMultiLineEqual
not_almost_equal              assertNotAlmostEqual
not_equal                     assertNotEqual
not_in                        assertNotIn
not_is_instance               assertNotIsInstance
not_regexp_matches            assertNotRegexpMatches
raises                        assertRaises
raises_regexp                 assertRaisesRegexp
regexp_matches                assertRegexpMatches
sequence_equal                assertSequenceEqual
set_equal                     assertSetEqual
true                          assertTrue
tuple_equal                   assertTupleEqual
"""

import unittest


class MethodMaker(object):
    def __init__(self):
        class Dummy(unittest.TestCase):
            def nop():
                pass

        self.t = Dummy('nop')

    def make_func(self, func_name, method_name):
        method = getattr(self.t, method_name)

        def func(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except AssertionError as e:
                raise e

        func.__name__ = func_name
        func.__doc__ = method.__doc__

        return func


_m = MethodMaker


almost_equal         = _m.make_func('almost_equal',         'assertAlmostEqual')
dict_contains_subset = _m.make_func('dict_contains_subset', 'assertDictContainsSubset')
dict_equal           = _m.make_func('dict_equal',           'assertDictEqual')
equal                = _m.make_func('equal',                'assertEqual')
false                = _m.make_func('false',                'assertFalse')
greater              = _m.make_func('greater',              'assertGreater')
greater_equal        = _m.make_func('greater_equal',        'assertGreaterEqual')
in_                  = _m.make_func('in_',                  'assertIn')
is_                  = _m.make_func('is_',                  'assertIs')
is_instance          = _m.make_func('is_instance',          'assertIsInstance')
is_none              = _m.make_func('is_none',              'assertIsNone')
is_not               = _m.make_func('is_not',               'assertIsNot')
is_not_none          = _m.make_func('is_not_none',          'assertIsNotNone')
items_equal          = _m.make_func('items_equal',          'assertItemsEqual')
less                 = _m.make_func('less',                 'assertLess')
less_equal           = _m.make_func('less_equal',           'assertLessEqual')
list_equal           = _m.make_func('list_equal',           'assertListEqual')
multi_line_equal     = _m.make_func('multi_line_equal',     'assertMultiLineEqual')
not_almost_equal     = _m.make_func('not_almost_equal',     'assertNotAlmostEqual')
not_equal            = _m.make_func('not_equal',            'assertNotEqual')
not_in               = _m.make_func('not_in',               'assertNotIn')
not_is_instance      = _m.make_func('not_is_instance',      'assertNotIsInstance')
not_regexp_matches   = _m.make_func('not_regexp_matches',   'assertNotRegexpMatches')
raises               = _m.make_func('raises',               'assertRaises')
raises_regexp        = _m.make_func('raises_regexp',        'assertRaisesRegexp')
regexp_matches       = _m.make_func('regexp_matches',       'assertRegexpMatches')
sequence_equal       = _m.make_func('sequence_equal',       'assertSequenceEqual')
set_equal            = _m.make_func('set_equal',            'assertSetEqual')
true                 = _m.make_func('true',                 'assertTrue')
tuple_equal          = _m.make_func('tuple_equal',          'assertTupleEqual')


del _m
del MethodMaker
