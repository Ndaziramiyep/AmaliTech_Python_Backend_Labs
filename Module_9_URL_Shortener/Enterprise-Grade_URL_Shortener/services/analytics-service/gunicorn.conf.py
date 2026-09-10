"""
Gunicorn tuning for analytics-service. Every knob is overridable via env
var, set in this service's own .env — gunicorn parses this file itself,
before it ever imports Config.wsgi/settings.py, so .env has to be loaded
here explicitly (django-environ, already a dependency) rather than relying
on Django to have done it first.

Bind is intentionally hardcoded, not env-driven: docker-compose.yml maps
host:8003 -> container:8000, so gunicorn must always listen on 8000 inside
the container regardless of PORT (which is a *different* setting, used only
by `manage.py runserver` for local, non-Docker runs).
"""

import multiprocessing
from pathlib import Path

import environ

env = environ.Env()
environ.Env.read_env(Path(__file__).resolve().parent / ".env")

bind = "0.0.0.0:8000"

# (2 x cores) + 1 is the standard sync/gthread starting point. Override
# directly when the container has a fixed CPU quota rather than the host's
# full core count.
workers = env.int("GUNICORN_WORKERS", default=multiprocessing.cpu_count() * 2 + 1)
worker_class = env("GUNICORN_WORKER_CLASS", default="gthread")
threads = env.int("GUNICORN_THREADS", default=4)

timeout = env.int("GUNICORN_TIMEOUT", default=30)
graceful_timeout = env.int("GUNICORN_GRACEFUL_TIMEOUT", default=30)
keepalive = env.int("GUNICORN_KEEPALIVE", default=5)

# Recycle each worker after N requests (+/- jitter, so they don't all recycle
# at once) — bounds any slow memory growth from a long-lived worker process.
max_requests = env.int("GUNICORN_MAX_REQUESTS", default=1000)
max_requests_jitter = env.int("GUNICORN_MAX_REQUESTS_JITTER", default=100)

# Loads the app once in the master before forking workers — shares code
# pages across workers instead of re-importing per worker. post_fork below
# closes the inherited DB connection so each worker opens its own.
preload_app = env.bool("GUNICORN_PRELOAD_APP", default=True)

accesslog = "-"
errorlog = "-"
loglevel = env("GUNICORN_LOG_LEVEL", default="info")
# %(D)s = request time in microseconds — a per-request latency signal in the
# access log itself, no profiling flag required to see it.
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sus'


def post_fork(server, worker):
    """A forked worker must not share the master's DB connection."""
    from django import db

    db.connections.close_all()
