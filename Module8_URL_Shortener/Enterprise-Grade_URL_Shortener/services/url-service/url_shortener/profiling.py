import cProfile
import pstats
import time
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


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
