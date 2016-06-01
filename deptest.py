#!/usr/bin/env python
# coding: utf-8

import os
import re
import sys
import imp
import logging
import traceback
# import functools
from collections import defaultdict


lg = logging.getLogger('deptest')


def gprint(s):
    """global print"""
    print s


def mprint(s):
    """module print"""
    print s


def fprint(s):
    """function print"""
    print s


def load_test_file(filepath):
    module_name = os.path.basename(filepath).split('.')[0]
    lg.debug('load module %s from %s', module_name, filepath)
    return imp.load_source(module_name, filepath)


def run_test_file(module):
    runner = ModuleRunner(module)
    runner.dispatch()


class ModuleRunner(object):
    entry_pattern = re.compile(r'^test_\w+$')
    module_setup_pattern = re.compile(r'^global_setup$')
    module_teardown_pattern = re.compile(r'^global_teardown$')

    def __init__(self, module):
        lg.debug('ModuleRunner init')
        entries = []
        entries_dict = {}
        module_setup = None
        module_teardown = None

        for name in dir(module):
            attr = getattr(module, name)

            # get entry
            if self.entry_pattern.match(name):
                lg.debug('match entry %s', name)

                # add essential attributes for entry
                if not hasattr(attr, 'dependencies'):
                    attr.dependencies = []

                entries.append(attr)
                entries_dict[attr.__name__] = attr
                continue

            # get setup
            if self.module_setup_pattern.match(name):
                lg.debug('match module_setup %s', name)
                module_setup = attr
                continue

            # get teardown
            if self.module_teardown_pattern.match(name):
                lg.debug('match module_teardown %s', name)
                module_teardown = attr
                continue

        self.entries = entries
        self.entries_dict = entries_dict
        self._traverse_entries()

        self.module_setup = module_setup
        self.module_teardown = module_teardown
        self.module = module

    def _traverse_entries(self):
        lg.debug('entries_dict: %s', self.entries_dict)
        for entry in self.entries:
            deps = traverse_entry_dependencies(entry, self.entries_dict)
            print 'entry {} depend on {}'.format(entry.__name__, deps)

    def dispatch(self):
        lg.debug('ModuleRunner dispatch')
        states = defaultdict(get_state)
        self._dispatch(self.entries, states)

    def _dispatch(self, entries, states):
        lg.debug('_dispatch')
        pendings = []

        for entry in entries:
            deps = traverse_entry_dependencies(entry, self.entries_dict)
            state = states[entry]
            if deps:
                if should_unmet(deps, states):
                    set_state(state, 'unmet', True)
                    self.log_entry_state(entry, state)
                    continue

                if should_pending(deps, states):
                    lg.debug('%s PENDING', entry)
                    pendings.append(entry)
                    continue

                self.run_entry(entry, states)
            else:
                self.run_entry(entry, states)

        if pendings:
            self._dispatch(pendings, states)

    def run_entry(self, entry, states):
        lg.debug('run entry %s', entry)
        state = states[entry]
        try:
            # get arguments
            entry()
        except Exception as e:
            str(e)
            # traceback
            traceback.print_exc()
            state['passed'] = False
        else:
            state['passed'] = True
        finally:
            state['executed'] = True

        self.log_entry_state(entry, state)

    def log_entry_state(self, entry, state):
        # log state
        if state['unmet']:
            status = 'UNMET'
        elif state['passed']:
            status = 'PASSED'
        else:
            status = 'FAILED'
        print '{}.{}... {}'.format(self.module.__name__, entry.__name__, status)


def get_state():
    return {
        'executed': False,
        'passed': False,
        'unmet': False,
        'return_value': None,
    }


def set_state(state, key, value):
    state[key] = value


def is_failed(state):
    return state['executed'] and not state['passed']


def should_unmet(deps, states):
    unmet = False
    # if any deps not PASSED or UNMET, should unmet
    for dep in deps:
        state = states[dep]
        if is_failed(state) or state['unmet']:
            unmet = True
    return unmet


def should_pending(deps, states):
    """First a entry is NOT UNMET, then consider if should pending,
    in other words, the prerequisite of PENDING is NOT UNMET
    """
    pending = False
    # if any deps not executed, should pending
    for dep in deps:
        state = states[dep]
        if not state['executed']:
            pending = True
    return pending


def traverse_entry_dependencies(entry, entries_dict, childs=None):
    if childs is None:
        childs = [entry]
    else:
        if entry not in childs:
            childs.append(entry)

    deps = []
    for i in entry.dependencies:
        dep = entries_dict[i['name']]
        #print 'entry', entry, 'dep', dep, 'childs', childs
        if dep in childs:
            raise ValueError(
                'recursive dependency detected: {} depend on {}'.format(entry.__name__, dep.__name__))
        deps.append(dep)
        merge_list(deps, traverse_entry_dependencies(dep, entries_dict, list(childs)))
    return deps


def merge_list(a, b):
    for i in b:
        if i not in a:
            a.append(i)


def depend_on(dep_name, with_return=False):
    def decorator_func(f):
        if not hasattr(f, 'dependencies'):
            f.dependencies = []
        # Avoid dep on self
        if dep_name == f.__name__:
            raise ValueError('Depend on self is not allowed')
        # Avoid duplicate dep
        if dep_name in [i['name'] for i in f.dependencies]:
            raise ValueError('Depend on one thing twice is not allowed')
        f.dependencies.append(
            {
                'name': dep_name,
                'with_return': with_return
            }
        )
        return f

    return decorator_func


def with_setup(setup_func=None, teardown_func=None):
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    filename = sys.argv[1]

    module = load_test_file(filename)

    run_test_file(module)
