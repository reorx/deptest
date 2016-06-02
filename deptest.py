#!/usr/bin/env python
# coding: utf-8

import os
import re
import sys
import imp
import logging
import argparse
import traceback
import threading
from StringIO import StringIO
# import functools
from collections import defaultdict, Counter


lg = logging.getLogger('deptest')

LINE_WIDTH = 70

config = {}


def gprint(s):
    """global print"""
    print s


def mprint(s):
    """module print"""
    print s


def fprint(s):
    """function print"""
    print s


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


def run_test_file(module):
    runner = ModuleRunner(module)
    runner.dispatch()
    return runner


class ModuleRunner(object):
    entry_pattern = re.compile(r'^test_\w+$')
    module_setup_pattern = re.compile(r'^global_setup$')
    module_teardown_pattern = re.compile(r'^global_teardown$')

    def __init__(self, path):
        module = self.load_module(path)

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

    def load_module(self, path):
        module = load_module_from_path(path)
        lg.debug('ModuleRunner init: %s', module)
        return module

    def _traverse_entries(self):
        lg.debug('entries_dict: %s', self.entries_dict)
        for entry in self.entries:
            deps = traverse_entry_dependencies(entry, self.entries_dict)
            lg.debug('entry {} depend on {}'.format(entry.__name__, deps))

    def dispatch(self):
        lg.debug('ModuleRunner dispatch')
        states = defaultdict(get_state)
        self.states = states
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
        entry_runner = EntryRunner(entry, state, self)
        entry_runner.run()

    def __str__(self):
        return '<ModuleRunner: {}>'.format(self.module.__name__)


class EntryRunner(object):
    def __init__(self, entry, state, module_runner):
        self.entry = entry
        self.state = state
        self.module_runner = module_runner
        self.stdout = []
        self._buf = None
        self.output = None

        # config
        self.clear = False

    def run(self):
        entry = self.entry
        state = self.state

        # capture_stdout
        self.capture_stdout()

        # capture_logging
        self.capture_logging()

        try:
            # TODO get arguments
            args = []
            for i in entry.dependencies:
                dep = self.module_runner.entries_dict[i['name']]
                dep_state = self.module_runner.states[dep]
                with_return = i['with_return']
                if with_return:
                    args.append(dep_state['return_value'])
                #lg.info('dep %s %s', dep, dep_state)
            state['return_value'] = entry(*args)
        except:
            state['traceback'] = traceback.format_exc()
            state['passed'] = False
        else:
            state['passed'] = True
        finally:
            state['executed'] = True

        # get output
        state['captured_stdout'] = self._get_buffer()

        # restore_stdout
        self.restore_stdout()

        # get logging
        state['captured_logging'] = self._get_logging()

        # restore_logging
        self.restore_logging()

        # log state
        self.log_state()

    def capture_stdout(self):
        self.stdout.append(sys.stdout)
        self._buf = StringIO()
        # Python 3's StringIO objects don't support setting encoding or errors
        # directly and they're already set to None.  So if the attributes
        # already exist, skip adding them.
        if (not hasattr(self._buf, 'encoding') and
                hasattr(sys.stdout, 'encoding')):
            self._buf.encoding = sys.stdout.encoding
        if (not hasattr(self._buf, 'errors') and
                hasattr(sys.stdout, 'errors')):
            self._buf.errors = sys.stdout.errors
        sys.stdout = self._buf

    def restore_stdout(self):
        while self.stdout:
            sys.stdout = self.stdout.pop()
        lg.debug('restored %s', sys.stdout)

    def capture_logging(self):
        print 'setup_log_handler in EntryRunner'
        setup_log_handler(config['log_handler'])

    def restore_logging(self):
        pass

    def _get_buffer(self):
        if self._buf is not None:
            return self._buf.getvalue()

    def _get_logging(self):
        return map(safe_str, config['log_handler'].buffer)

    def log_state(self):
        entry = self.entry
        state = self.state
        status = get_state_status(state)
        full_name = '{}.{}'.format(self.module_runner.module.__name__, entry.__name__)

        if status == 'FAILED':
            print '=' * LINE_WIDTH
            print '{}... {}'.format(full_name, status)
            print '-' * LINE_WIDTH
            print state['traceback']
            print '-------------------- >> begin captured stdout << ---------------------'
            print state['captured_stdout']
            print '--------------------- >> end captured stdout << ----------------------'
            print ''
            print '-------------------- >> begin captured logging << ---------------------'
            print '\n'.join(state['captured_logging'])
            print '--------------------- >> end captured logging << ----------------------'
            print ''
            print '-' * LINE_WIDTH
        else:
            print '{}... {}'.format(full_name, status)


def setup_log_handler(log_handler, clear=False):
    print 'setupLoghandler'
    # setup our handler with root logger
    root_logger = logging.getLogger()
    if clear:
        if hasattr(root_logger, "handlers"):
            for handler in root_logger.handlers:
                root_logger.removeHandler(handler)
        for logger in logging.Logger.manager.loggerDict.values():
            if hasattr(logger, "handlers"):
                for handler in logger.handlers:
                    logger.removeHandler(handler)
    # make sure there isn't one already
    # you can't simply use "if log_handler not in root_logger.handlers"
    # since at least in unit tests this doesn't work --
    # LogCapture() is instantiated for each test case while root_logger
    # is module global
    # so we always add new MyMemoryHandler instance
    for handler in root_logger.handlers[:]:
        if isinstance(handler, MyMemoryHandler):
            root_logger.handlers.remove(handler)
    root_logger.addHandler(log_handler)
    print 'handlers', root_logger.handlers
    # to make sure everything gets captured
    loglevel = "NOTSET"
    root_logger.setLevel(getattr(logging, loglevel))


def get_state():
    return {
        'unmet': False,
        'executed': False,
        'passed': False,
        'return_value': None,
        'traceback': None,
        'captured_stdout': None,
        'captured_logging': None,
    }


def get_state_status(state):
    if state['unmet']:
        status = 'UNMET'
    elif state['passed']:
        status = 'PASSED'
    else:
        status = 'FAILED'
    return status


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


_ignore_dirs = ['.git']


_test_file_pattern = re.compile(r'^(.+_test|test_.+)\.py$')


def walk_dir(dirpath, filepaths):
    for root, dirs, files in os.walk(dirpath):
        for name in files:
            if _test_file_pattern.match(name):
                filepath = os.path.join(root, name)
                filepaths.append(filepath)

        for dir in dirs:
            if dir in _ignore_dirs:
                lg.debug('ignore %s %s', root, dir)
                dirs.remove(dir)


def log_summary(runners):
    summary = Counter({'UNMET': 0, 'PASSED': 0, 'FAILED': 0, 'total': 0})
    for runner in runners:
        lg.debug('runner %s', runner)
        if not runner.entries:
            continue
        for entry, state in runner.states.iteritems():
            status = get_state_status(state)
            summary[status] += 1
            summary['total'] += 1

    print '\n' + '-' * LINE_WIDTH
    print 'Ran {total} tests, PASSED {PASSED}, FAILED {FAILED}, UNMET {UNMET}'.format(**summary)


class MyMemoryHandler(logging.Handler):
    def __init__(self, logformat, logdatefmt=None, filters=None):
        logging.Handler.__init__(self)
        fmt = logging.Formatter(logformat, logdatefmt)
        self.setFormatter(fmt)
        if filters is None:
            filters = ['-deptest']
        self.filterset = FilterSet(filters)
        self.buffer = []

    def emit(self, record):
        self.buffer.append(self.format(record))

    def flush(self):
        pass

    def truncate(self):
        self.buffer = []

    def filter(self, record):
        print 'name', record.name
        if self.filterset.allow(record.name):
            print 'allow', record.name
            return logging.Handler.filter(self, record)

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['lock']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.lock = threading.RLock()


class FilterSet(object):
    def __init__(self, filter_components):
        self.inclusive, self.exclusive = self._partition(filter_components)

    # @staticmethod
    def _partition(components):
        inclusive, exclusive = [], []
        for component in components:
            if component.startswith('-'):
                exclusive.append(component[1:])
            else:
                inclusive.append(component)
        return inclusive, exclusive
    _partition = staticmethod(_partition)

    def allow(self, record):
        """returns whether this record should be printed"""
        if not self:
            # nothing to filter
            return True
        return self._allow(record) and not self._deny(record)

    # @staticmethod
    def _any_match(matchers, record):
        """return the bool of whether `record` starts with
        any item in `matchers`"""
        def record_matches_key(key):
            return record == key or record.startswith(key + '.')
        return anyp(bool, map(record_matches_key, matchers))
    _any_match = staticmethod(_any_match)

    def _allow(self, record):
        if not self.inclusive:
            return True
        return self._any_match(self.inclusive, record)

    def _deny(self, record):
        if not self.exclusive:
            return False
        return self._any_match(self.exclusive, record)


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


def set_logger(name,
               level=logging.INFO,
               fmt='%(name)s %(levelname)s %(message)s',
               propagate=1):
    """
    This function will clear the previous handlers and set only one handler,
    which will only be StreamHandler for the logger.

    This function is designed to be able to called multiple times in a context.

    Note that if a logger has no handlers, it will be added a handler automatically when it is used.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate

    handler = None
    for h in logger.handlers:
        if isinstance(h, logging.StreamHandler):
            # use existing instead of clean and create
            handler = h
            break
    if not handler:
        handler = logging.StreamHandler()
        logger.addHandler(handler)

    handler.setFormatter(logging.Formatter(fmt=fmt))


def main():
    # the `formatter_class` can make description & epilog show multiline
    parser = argparse.ArgumentParser(description="", epilog="", formatter_class=argparse.RawDescriptionHelpFormatter)

    # arguments
    parser.add_argument('paths', metavar="PATH", type=str, help="files or dirs to scan", nargs='+')

    # options
    parser.add_argument('-a', '--aa', type=int, default=0, help="")
    parser.add_argument('-b', '--bb', type=str, help="")
    parser.add_argument('-s', '--nocapture', action='store_true', help="Don't capture stdout (any stdout output will be printed immediately)")
    parser.add_argument('--debug', action='store_true', help="Set logging level to debug for deptest logger")

    args = parser.parse_args()

    print 'setup_log_handler in global'
    logformat = '%(name)s: %(levelname)s: %(message)s'
    config['log_handler'] = MyMemoryHandler(logformat)
    setup_log_handler(config['log_handler'])

    if args.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    # format='[%(levelname)s %(module)s:%(lineno)d] %(message)s')

    set_logger('deptest', level=logging_level, propagate=0)

    filepaths = []

    for path in args.paths:
        if os.path.isdir(path):
            walk_dir(path, filepaths)
        else:
            filepaths.append(path)

    runners = []
    for filepath in filepaths:
        runner = ModuleRunner(filepath)
        runners.append(runner)
        runner.dispatch()

    log_summary(runners)


if __name__ == '__main__':
    main()
