__author__ = 'Benjamin Knight'
__license__ = 'MIT'
__version__ = '0.1'


def _fix_vendored():
    import importlib
    import os
    import os.path
    import sys

    vendored = (
        'charset_normalizer',
        'certifi',
        'colour',
        'idna',
        os.path.join('png', 'code'),
        'requests',
        os.path.join('urllib3', 'src'),
        'workflow',
        os.path.join('yaml', 'lib'),
    )
    vendored_dir = os.path.join(os.path.dirname(__file__), 'packages')
    sys.path = sys.path[0:1] + [os.path.join(vendored_dir, p) for p in vendored] + sys.path[1:]

    # Make sure that `workflow.background` sees our terrible mutated path
    os.environ['PYTHONPATH'] = ':'.join(sys.path)

    importlib.invalidate_caches()

    from workflow.workflow import PickleSerializer, manager as serializer_manager
    serializer_manager.register('cpickle', PickleSerializer)


_fix_vendored()
del _fix_vendored
