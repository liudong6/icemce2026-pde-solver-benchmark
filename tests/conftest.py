"""Make optional CUDA validation explicit without hiding required GPU failures."""
import pytest


def pytest_addoption(parser):
    parser.addoption('--require-cuda', action='store_true', default=False,
                     help='Fail if CUDA is unavailable instead of skipping GPU tests.')


def pytest_configure(config):
    config.addinivalue_line('markers', 'cuda: requires the optional working CUDA runtime and device')


def pytest_collection_modifyitems(config, items):
    from numba import cuda

    available = cuda.is_available()
    if config.getoption('--require-cuda') and not available:
        raise pytest.UsageError('--require-cuda was requested, but CUDA is unavailable')
    if not available:
        skip = pytest.mark.skip(reason='Optional CUDA runtime/device unavailable; use --require-cuda to require it')
        for item in items:
            if item.get_closest_marker('cuda'):
                item.add_marker(skip)
