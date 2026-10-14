ARG BUILDER_IMAGE=registry.access.redhat.com/ubi9/python-312:latest

FROM ${BUILDER_IMAGE} AS builder

USER 0
WORKDIR /opt/app-root/src

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Konflux hermetic builds override BUILDER_IMAGE to uv-builder-rhel9, which
# already ships uv and has no pip3.12. The default UBI Python image still
# needs the pip install. Do not reach PyPI when uv is already on PATH.
RUN (command -v uv >/dev/null 2>&1 || pip3.12 install --no-cache-dir uv==0.12.3) \
    && [ -f /usr/local/bin/uv ] || ln -s "$(command -v uv)" /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md alembic.ini ./
COPY src/ ./src/

# Hermetic Konflux: cachi2.env injects PIP_FIND_LINKS; stay offline.
# Local and GitHub Actions builds fall through to a normal uv sync.
RUN if [ -n "${PIP_FIND_LINKS:-}" ]; then \
        uv sync --frozen --no-dev --no-editable --no-index --find-links "${PIP_FIND_LINKS}" --offline; \
    else \
        uv sync --frozen --no-dev --no-editable; \
    fi

FROM registry.access.redhat.com/ubi9/ubi-minimal:latest@sha256:8eb2830d0936237fc13a1f2f7e45aecf90d69043380ad167fad0343632937f41 AS runtime

USER 0

RUN microdnf install --setopt=install_weak_deps=0 --nodocs -y python3.12 python3.12-pip python3.12-cffi \
    && microdnf clean all

RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

WORKDIR /opt/app-root/src
COPY LICENSE /licenses/LICENSE
COPY --from=builder /opt/app-root/src/alembic.ini ./alembic.ini
COPY --from=builder /opt/app-root/src/src/execution_plane/migrations ./src/execution_plane/migrations
COPY --from=builder /opt/app-root/src/.venv /opt/app-root/src/.venv
COPY --from=builder /opt/app-root/src/alembic.ini /opt/app-root/src/alembic.ini
COPY --from=builder /opt/app-root/src/src /opt/app-root/src/src

ENV PATH="/opt/app-root/src/.venv/bin:/opt/app-root/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chown -R 1001:0 /opt/app-root && chmod -R g=u /opt/app-root

USER 1001

CMD ["python3", "-m", "execution_plane.worker"]
