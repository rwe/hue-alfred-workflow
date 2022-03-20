__author__ = 'Benjamin Knight'
__license__ = 'MIT'
__version__ = '0.1'


def _fix_vendored():
    import importlib
    import os
    import os.path
    import sys

    vendored_dir = os.path.join(os.path.dirname(__file__), 'packages')
    sys.path = sys.path[0:1] + [vendored_dir] + sys.path[1:]

    # Make sure that `workflow.background` sees our terrible mutated path
    os.environ['PYTHONPATH'] = ':'.join(sys.path)

    importlib.invalidate_caches()


_fix_vendored()
del _fix_vendored
