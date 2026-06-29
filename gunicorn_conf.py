"""Gunicorn config for the container. Kept as a file (not flags) so it is
diffable and reviewable in a PR like any other piece of config.
"""

import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# 2x+1 is the gunicorn-recommended starting point for CPU-bound workers.
# Capped at 4 because this runs on small instances (t2.micro/t3.micro) in
# the reference Terraform; uncapped, it would over-provision threads on a
# bigger box for no benefit and just burn memory.
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)
worker_class = "sync"
timeout = 30
graceful_timeout = 30
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

# Container orchestrators send SIGTERM on shutdown; give in-flight requests
# `graceful_timeout` seconds to finish instead of dropping them mid-response.
