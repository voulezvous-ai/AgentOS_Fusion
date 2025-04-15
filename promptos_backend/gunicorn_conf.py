
import os
import multiprocessing
from app.core.config import settings

_workers_default = (multiprocessing.cpu_count() * 2) + 1

bind = settings.GUNICORN_BIND
workers = settings._GUNICORN_WORKERS or _workers_default
worker_class = settings.GUNICORN_WORKER_CLASS

accesslog = '-'
errorlog = '-'
loglevel = settings.LOG_LEVEL.lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

preload_app = False

print(f"Gunicorn config loaded: Binding to {bind}, Workers: {workers}, Class: {worker_class}, LogLevel: {loglevel}")
