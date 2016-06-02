#!/usr/bin/env python
# coding: utf-8


class Config(object):
    _internal_keys = ['keys', 'args_keys', 'parser']

    def __init__(self):
        self.keys = []
        self.args_keys = []
        self.parser = None

    def register_parser(self, parser):
        self.parser = parser

    def define(self, key, typ):
        self.keys.append(key)

        if typ == 'args':
            self.args_keys.append(key)
            setattr(self, key, NotImplementedError)
        else:
            setattr(self, key, None)

    def __setattr__(self, key, value):
        if key not in self._internal_keys and key not in self.keys:
            raise ValueError('%s is not defined in config' % key)
        super(Config, self).__setattr__(key, value)

    def parse_args(self):
        args = self.parser.parse_args()

        for i in self.args_keys:
            setattr(self, i, getattr(args, i))

    def __str__(self):
        return '<Config: {}>'.format(
            ','.join('{}={}'.format(i, getattr(self, i)) for i in self.keys)
        )
