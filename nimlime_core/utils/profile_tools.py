try:
    from cProfile import Profile
except ImportError:
    from profile import Profile
from pstats import Stats
from functools import wraps

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
profiler = Profile()
running = False


def print_profile_data():
    stream = StringIO()
    statistics = Stats(profiler, stream=stream)
    statistics.sort_stats('cumulative')
    statistics.print_stats()
    print(stream.getvalue())


def profile_func(func):
    @wraps(func)
    def profile_wrapper(*args, **kwargs):
        global running
        if not running:
            running = True
            try:
                profiler.enable()
                return func(*args, **kwargs)
            finally:
                profiler.disable()
                running = False

    return profile_wrapper
