# The sandbox image. bigbrother.sandbox.ensure_image() builds it once as
# bigbrother-sandbox:0.1. The install and run containers both use it.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /usr/local/bin/uv

# /deps belongs to the sandbox user so a fresh named volume mounted there
# starts out writable by uid 1000.
RUN useradd --uid 1000 --create-home sandbox \
    && mkdir /src /deps \
    && chown sandbox:sandbox /deps

USER 1000:1000
WORKDIR /tmp
