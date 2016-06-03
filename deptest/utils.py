# coding: utf-8

LINE_WIDTH = 70

# in PY3, its str
unicode_type = unicode

_TO_UNICODE_TYPES = (unicode_type, type(None))


def to_unicode(value):
    """Converts a string argument to a unicode string.

    If the argument is already a unicode string or None, it is returned
    unchanged.  Otherwise it must be a byte string and is decoded as utf8.
    """
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    if not isinstance(value, bytes):
        raise TypeError(
            "Expected bytes, unicode, or None; got %r" % type(value)
        )
    return value.decode("utf-8")


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
        return unicode(val).encode(encoding)


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
