# coding: utf-8

import os
import re
import sys
import logging
import argparse
import traceback
from StringIO import StringIO
from collections import defaultdict, Counter

from .loader import load_module_from_path
from .utils import ln, hr, safe_str, merge_list, ObjectDict
from .log import setup_log_handler, MyMemoryHandler, set_logger, color
from .config_object import Config


lg = logging.getLogger('deptest')

config = Config()

STATUS_NAMES = ['OK', 'FAILED', 'UNMET']

STATUS_COLORS = {
    'OK': 'green',
    'FAILED': 'red',
    'UNMET': 'yellow',
}

COLORED_STATUSES = {i: color.dye(STATUS_COLORS[i], i) for i in STATUS_NAMES}


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
                    self.run_entry(entry, states)
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

        if state['unmet']:
            lg.debug('%s UNMET, skip run', entry.__name__)
            self.log_state()
            return

        self.before()

        try:
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
            state['ok'] = False
        else:
            state['ok'] = True
        finally:
            state['executed'] = True

        self.after()

        # log state
        self.log_state()

    def before(self):
        if not config.nocapture:
            # capture_stdout
            self.capture_stdout()

        if not config.nologcapture:
            # capture_logging
            self.capture_logging()

    def after(self):
        state = self.state

        if not config.nocapture:
            # get output
            state['captured_stdout'] = self._get_buffer()

            # restore_stdout
            self.restore_stdout()

        if not config.nologcapture:
            # get logging
            state['captured_logging'] = self._get_logging()

            # restore_logging
            self.restore_logging()

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
        lg.debug('stdout restored %s', sys.stdout)

    def capture_logging(self):
        lg.debug('call setup_log_handler in EntryRunner')
        setup_log_handler(config.log_handler)

    def restore_logging(self):
        pass

    def _get_buffer(self):
        if self._buf is not None:
            return self._buf.getvalue()

    def _get_logging(self):
        l = map(safe_str, config.log_handler.buffer)
        config.log_handler.truncate()
        return l

    # _prompt_symbol = '➔'
    # _prompt_symbol = '➤'
    _prompt_symbol = '→'

    def log_state(self):
        entry = self.entry
        state = self.state
        status = get_state_status(state)
        full_name = '{}.{}'.format(self.module_runner.module.__name__, entry.__name__)

        start_line = '{} {}... {}'.format(
            color.dye('blue', self._prompt_symbol),
            color.dye('blue', full_name),
            color.dye(STATUS_COLORS[status], status))

        print start_line
        if status == 'FAILED':
            # print hr('=')
            # print hr('-')
            print hr('=')
            print state['traceback']
            if not config.nocapture and state['captured_stdout']:
                print ln('>> begin captured stdout <<')
                print state['captured_stdout']
                print ln('>> end captured stdout <<')
            if not config.nologcapture and state['captured_logging']:
                print ln('>> begin captured logging <<')
                print '\n'.join(state['captured_logging'])
                print ln('>> end captured logging <<')
            print hr('-')
            print ''
        else:
            pass


def log_summary(runners):
    summary = {'UNMET': 0, 'OK': 0, 'FAILED': 0, 'total': 0}
    for runner in runners:
        lg.debug('runner %s', runner)
        if not runner.entries:
            continue
        for entry, state in runner.states.iteritems():
            status = get_state_status(state)
            summary[status] += 1
            summary['total'] += 1

    colored_statuses = {i: (i if summary[i] == 0 else COLORED_STATUSES[i]) for i in STATUS_NAMES}

    print hr('_')
    print 'Ran {s.total} tests, {c.OK} {s.OK}, {c.FAILED} {s.FAILED}, {c.UNMET} {s.UNMET}'.format(
        s=ObjectDict(summary),
        c=ObjectDict(colored_statuses))


def get_state():
    return {
        'unmet': False,
        'executed': False,
        'ok': False,
        'return_value': None,
        'traceback': None,
        'captured_stdout': None,
        'captured_logging': None,
    }


def get_state_status(state):
    if state['unmet']:
        status = 'UNMET'
    elif state['ok']:
        status = 'OK'
    else:
        status = 'FAILED'
    return status


def set_state(state, key, value):
    state[key] = value


def is_failed(state):
    return state['executed'] and not state['ok']


def should_unmet(deps, states):
    unmet = False
    # if any deps not OK or UNMET, should unmet
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
                lg.debug('ignore %s at %s', dir, root)
                dirs.remove(dir)


def define_config(parser):
    config.register_parser(parser)

    config.define('nocapture', 'args')
    parser.add_argument('-s', '--nocapture', action='store_true', help="Don't capture stdout (any stdout output will be printed immediately)")

    config.define('nologcapture', 'args')
    parser.add_argument('--nologcapture', action='store_true', help="Don't capture logging")

    config.define('dry', 'args')
    parser.add_argument('--dry', action='store_true', help="Dry run, only show matched files")

    config.define('debug', 'args')
    parser.add_argument('--debug', action='store_true', help="Set logging level to debug for deptest logger")

    config.define('paths', 'args')
    parser.add_argument('paths', metavar="PATH", type=str, help="files or dirs to scan", nargs='*', default='.')

    config.define('log_handler', None)


def main():
    # the `formatter_class` can make description & epilog show multiline
    parser = argparse.ArgumentParser(description="", epilog="", formatter_class=argparse.RawDescriptionHelpFormatter)

    define_config(parser)

    config.parse_args()

    if config.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    set_logger('deptest', level=logging_level, propagate=0,
               fmt='[%(levelname)s %(module)s:%(lineno)d] %(message)s')

    lg.debug('config: %s', config)

    if not config.nologcapture:
        logformat = '%(name)s: %(levelname)s: %(message)s'
        config.log_handler = MyMemoryHandler(logformat)

        lg.debug('call setup_log_handler in global')
        setup_log_handler(config.log_handler)

    filepaths = []

    for path in config.paths:
        if os.path.isdir(path):
            walk_dir(path, filepaths)
        else:
            filepaths.append(path)

    if config.dry:
        for i in filepaths:
            print i
        return

    runners = []
    for filepath in filepaths:
        runner = ModuleRunner(filepath)
        runners.append(runner)
        runner.dispatch()

    log_summary(runners)
