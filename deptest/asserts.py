# coding: utf-8

"""Assert functions to make tests easier

these functions are exported from methods of unitest.TestCase class,
the original camel case name is converted to underscore style,
below is a complete list of function names compare to unittest method names:

almost_equal                  assertAlmostEqual
almost_equals                 assertAlmostEquals
dict_contains_subset          assertDictContainsSubset
dict_equal                    assertDictEqual
equal                         assertEqual
equals                        assertEquals
false                         assertFalse
greater                       assertGreater
greater_equal                 assertGreaterEqual
in                            assertIn
is                            assertIs
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
not_almost_equals             assertNotAlmostEquals
not_equal                     assertNotEqual
not_equals                    assertNotEquals
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

import re
import unittest
from .utils import camel_to_underscore

__all__ = []


def _export_assert_methods():
    name_regex = re.compile('^assert([a-zA-Z]+)$')

    class Dummy(unittest.TestCase):
        def nop():
            pass

    t = Dummy('nop')

    for i in dir(t):
        m = name_regex.search(i)
        if not m:
            continue

        camel_name = m.groups()[0]
        name = camel_to_underscore(camel_name)
        print '{:<30}{}'.format(name, i)

        method = getattr(t, i)

        # expose to globals
        globals()[name] = method

        # expose to __all__
        __all__.append(name)


_export_assert_methods()
