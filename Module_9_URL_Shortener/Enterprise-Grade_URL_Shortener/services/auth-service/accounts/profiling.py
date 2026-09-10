import cProfile
import functools
import pstats
import time
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


def _append_to_profile_log(header, body):
    """Appends one profiling run's output to logs/profiling.log, timestamped."""
    log_path = Path(settings.BASE_DIR) / "logs" / "profiling.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 88}\n{header}\n{'=' * 88}\n{body}\n")


def profile_function(func):
    """
    Wraps `func` with cProfile and appends its stats (top 20 by cumulative
    time) to logs/profiling.log on every call — for measuring one function's
    own performance and its call graph, as opposed to ProfilingMiddleware's
    whole-request view. No-op unless settings.PROFILING_ENABLED is on
    (env ENABLE_PROFILING), so it costs nothing when profiling is off.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.PROFILING_ENABLED:
            return func(*args, **kwargs)

        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return func(*args, **kwargs)
        finally:
            profiler.disable()
            buffer = StringIO()
            pstats.Stats(profiler, stream=buffer).sort_stats("cumulative").print_stats(20)
            _append_to_profile_log(
                f"[cProfile] {func.__module__}.{func.__qualname__} — {time.strftime('%Y-%m-%d %H:%M:%S')}",
                buffer.getvalue(),
            )

    return wrapper


def profile_lines(func):
    """
    Wraps `func` with line_profiler and appends its per-line timing to
    logs/profiling.log on every call — for finding which specific line(s)
    inside one function are the actual cost, not just the function as a
    whole. Requires the `line_profiler` package (see requirements.txt);
    imported lazily so its absence only breaks a call to a function actually
    decorated with this, not the whole app. No-op unless
    settings.PROFILING_ENABLED is on.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.PROFILING_ENABLED:
            return func(*args, **kwargs)

        from line_profiler import LineProfiler

        profiler = LineProfiler()
        profiled = profiler(func)
        try:
            return profiled(*args, **kwargs)
        finally:
            buffer = StringIO()
            profiler.print_stats(stream=buffer)
            _append_to_profile_log(
                f"[line_profiler] {func.__module__}.{func.__qualname__} — {time.strftime('%Y-%m-%d %H:%M:%S')}",
                buffer.getvalue(),
            )

    return wrapper


class ProfilingMiddleware:
    """
    Profiles one request end-to-end with cProfile when both
    settings.PROFILING_ENABLED (env ENABLE_PROFILING) is on and the request
    carries `?profile=1` — opt-in on both ends so nothing is profiled by
    accident in production.

    `?profile=1&format=text` returns the top 30 cumulative-time stack frames
    inline. `?profile=1` alone dumps the full stats to logs/profiles/ for
    offline inspection, e.g. `snakeviz logs/profiles/<file>.prof`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.PROFILING_ENABLED or request.GET.get("profile") != "1":
            return self.get_response(request)

        profiler = cProfile.Profile()
        profiler.enable()
        response = self.get_response(request)
        profiler.disable()

        if request.GET.get("format") == "text":
            buffer = StringIO()
            pstats.Stats(profiler, stream=buffer).sort_stats("cumulative").print_stats(30)
            return HttpResponse(buffer.getvalue(), content_type="text/plain")

        profile_dir = Path(settings.BASE_DIR) / "logs" / "profiles"
        profile_dir.mkdir(parents=True, exist_ok=True)
        slug = request.path.strip("/").replace("/", "_") or "root"
        profiler.dump_stats(profile_dir / f"{slug}-{int(time.time() * 1000)}.prof")

        return response
