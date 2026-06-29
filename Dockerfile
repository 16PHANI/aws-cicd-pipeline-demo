# Multi-stage build: the "builder" stage has gcc/headers for anything that
# needs to compile a wheel, the runtime stage is python:3.11-slim with
# nothing but the installed packages and app code copied in. Cuts the
# final image down and keeps build tooling off the box that runs in prod.

FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.11-slim AS runtime

# Pin a non-root, non-zero UID/GID so the container never runs as root and
# so the same numeric UID works whether or not the image is run on a host
# that has a matching /etc/passwd entry (Kubernetes doesn't care, but a
# bare `docker run` on a misconfigured host might).
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /usr/sbin/nologin --no-create-home appuser

COPY --from=builder /install /usr/local

WORKDIR /app
COPY app/ ./app/
COPY gunicorn_conf.py .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:5000/health', timeout=2)" || exit 1

CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
