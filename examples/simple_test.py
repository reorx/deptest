# coding: utf-8

from deptest import depend_on


@depend_on('test_c', with_return=True)
@depend_on('test_b', with_return=True)
def test_a(name1, name2):
    print 'a, depend on', name1, name2
    return 'a', 'aa'


@depend_on('test_d')
def test_b():
    print 'b'
    return 'b'


@depend_on('test_d')
def test_c():
    print 'c'
    return 'c'


def test_d():
    print 'd'
    return 'd'


@depend_on('test_a', with_return=True)
def test_e(v):
    print 'e get', v
    return 'e'
