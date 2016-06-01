#!/usr/bin/env python
# coding: utf-8

from deptest import depend_on

print 'import simple test'

g = 'aaa'


@depend_on('test_d', with_return=True)
@depend_on('test_b')
@depend_on('test_c', with_return=True)
def test_a(x, y):
    print 'func a depend on b & c'
    print 'func a get args', x, y
    #print 'g is', g
    assert 0
    return 'a'


@depend_on('test_c')
def test_b():
    print 'func b'
    #print 'g is', g
    return 'b'


@depend_on('test_d')
def test_c():
    print 'func c'
    return 'c'


def test_d():
    print 'func d'
    return 'd'
