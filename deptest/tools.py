# coding: utf-8
#
# Copy from (nose)[http://nose.readthedocs.io/en/latest/]:
# - nose.tools.with_setup

"""Tools to help writing tests
"""


def with_setup(setup=None, teardown=None):
    """Decorator to add setup and/or teardown methods to a test function::

      @with_setup(setup, teardown)
      def test_something():
          " ... "

    Note that `with_setup` is useful *only* for test functions, not for test
    methods or inside of TestCase subclasses.
    """
    def decorate(func, setup=setup, teardown=teardown):
        if setup:
            if hasattr(func, 'setup'):
                _old_s = func.setup

                def _s():
                    setup()
                    _old_s()
                func.setup = _s
            else:
                func.setup = setup
        if teardown:
            if hasattr(func, 'teardown'):
                _old_t = func.teardown

                def _t():
                    _old_t()
                    teardown()
                func.teardown = _t
            else:
                func.teardown = teardown
        return func
    return decorate
