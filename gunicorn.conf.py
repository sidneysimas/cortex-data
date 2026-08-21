"""
Gunicorn config for running Data Formulator as a real WSGI server instead
of Flask's single-threaded dev server (which is what caused the app to
lock up entirely whenever one request got stuck — see project notes,
Aug 2026).

Single worker process, multiple threads:
  - Keeps one shared Python process (matches the app's assumptions: the
    in-process model registry and credential vault aren't designed for
    multiple independent worker processes).
  - Threads (not a single sync worker) mean one slow/stuck LLM call no
    longer blocks every other request — the original failure mode.

Long timeout: LLM calls (especially local Ollama models) can legitimately
take several minutes. This must stay well above that so gunicorn doesn't
kill and restart the worker mid-request.
"""
import os

bind = f"{os.environ.get('HOST', '127.0.0.1')}:{os.environ.get('PORT', '5567')}"
workers = 1
worker_class = "gthread"
threads = int(os.environ.get("GUNICORN_THREADS", "8"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "1800"))  # 30 min
graceful_timeout = 30
keepalive = 5

# Flask's own per-request "werkzeug - INFO - GET /..." log lines only show
# up when werkzeug's dev server handles the request loop directly. Under
# gunicorn that loop is gone, so gunicorn's own access log takes over the
# same job — needed, this has been the primary tool for diagnosing issues.
accesslog = "-"    # stdout, picked up by the systemd journal
access_log_format = '%(t)s "%(r)s" %(s)s %(b)s %(L)ss'
errorlog = "-"      # stderr, picked up by the systemd journal
loglevel = "info"
