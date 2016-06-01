#!/usr/bin/env python
# coding: utf-8

from deptest import depend_on

print 'import simple test'

g = 'aaa'


@depend_on('test_d')
@depend_on('test_b')
@depend_on('test_c')
def test_a():
    print 'func a depend on b & c'
    #print 'g is', g


@depend_on('test_c')
def test_b():
    print 'func b'
    #print 'g is', g


@depend_on('test_d')
def test_c():
    print 'func c'


def test_d():
    print 'func d'
