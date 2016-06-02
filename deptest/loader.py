#!/usr/bin/env python
# coding: utf-8

import os
import sys
import imp
import logging

lg = logging.getLogger('deptest.loader')


def load_module_from_path(filepath):
    # add path
    dirpath = os.path.dirname(filepath)
    sys.path.insert(0, dirpath)

    module_name = os.path.basename(filepath).split('.')[0]
    lg.debug('load module %s from %s, at %s', module_name, filepath, os.getcwd())
    module = imp.load_source(module_name, filepath)

    # remove path
    del sys.path[0]

    return module
