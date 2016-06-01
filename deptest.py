#!/usr/bin/env python
# coding: utf-8

import os
import re
import sys
import imp


def global_log(s):
    print s


def module_log(s):
    print s


def func_log(s):
    print s


def load_test_file(filepath):
    module_name = os.path.basename(filepath).split('.')[0]
    return imp.load_source(module_name, filepath)


def run_test_file(module):
    runner = ModuleRunner(module)
    runner.dispatch()


class ModuleRunner(object):
    entry_pattern = re.compile(r'^test_\w+$')
    module_setup_pattern = re.compile(r'^global_setup$')
    module_teardown_pattern = re.compile(r'^global_teardown$')

    def __init__(self, module):
        entries = []
        module_setup = None
        module_teardown = None

        for name in dir(module):
            attr = getattr(module, name)
            # get entry
            if self.entry_pattern.match(name):
                entries.append(attr)
                continue

            # get setup
            if self.module_setup_pattern.match(name):
                module_setup = attr
                continue

            # get teardown
            if self.module_teardown_pattern.match(name):
                module_teardown = attr
                continue

        self.entries = entries
        self.module_setup = module_setup
        self.module_teardown = module_teardown

    def dispatch(self):
        for entry in self.entries:
            self.run_entry(entry)

    def run_entry(self, entry):
        print 'run entry', entry
        entry()


if __name__ == '__main__':
    filename = sys.argv[1]

    module = load_test_file(filename)

    run_test_file(module)
