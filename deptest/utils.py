# coding: utf-8

"""Util functions for deptest project, unlike tools, it's only for internal use
"""

import re
import sys


PY2 = sys.version_info.major < 3

LINE_WIDTH = 70

# in PY3, its str
unicode_type = str


def to_str(value):
    if PY2:
        if isinstance(value, unicode):  # NOQA
            return value.encode('utf-8')
    return value


def ln(label, char='-'):
    """Draw a divider, with label in the middle.

    >>> ln('hello there')
    '---------------------------- hello there -----------------------------'
    """
    label_len = len(label) + 2
    chunk = (LINE_WIDTH - label_len) // 2
    out = '%s %s %s' % (char * chunk, label, char * chunk)
    pad = LINE_WIDTH - len(out)
    if pad > 0:
        out = out + (char * pad)
    return out


def hr(char='-'):
    return LINE_WIDTH * char


def anyp(predicate, iterable):
    for item in iterable:
        if predicate(item):
            return True
    return False


def safe_str(val, encoding='utf-8'):
    try:
        return str(val)
    except UnicodeEncodeError:
        if isinstance(val, Exception):
            return ' '.join([safe_str(arg, encoding)
                             for arg in val])
        return str(val).encode(encoding)


def merge_list(a, b):
    for i in b:
        if i not in a:
            a.append(i)


class ObjectDict(dict):
    """
    retrieve value of dict in dot style
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('Has no attribute %s' % key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

    def __str__(self):
        return '<ObjectDict %s >' % dict(self)


def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
