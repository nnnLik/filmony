ARG PYTHON_IMAGE=python:3.13-slim

FROM $PYTHON_IMAGE AS base

ENV PYTHONUNBUFFERED=1 \
	PYSETUP_PATH="/opt/pysetup" \
	VENV_PATH="/opt/pysetup/.venv" \
	APP_PATH="/opt/app" \
	PYTHONPATH="/opt/app/src"

RUN apt-get update && \
	pip install uv==0.9.2 && \
	rm -rf /var/lib/apt/lists/*

WORKDIR $PYSETUP_PATH

FROM base AS builder

COPY pyproject.toml uv.lock $PYSETUP_PATH/
RUN uv sync --group=prod
ENV PATH="$VENV_PATH/bin:$PATH"

FROM builder AS dev

RUN uv sync --group=dev

COPY --from=builder $VENV_PATH $VENV_PATH
COPY . ${APP_PATH}

WORKDIR ${APP_PATH}

FROM builder AS prod

COPY --from=builder $VENV_PATH $VENV_PATH
COPY . ${APP_PATH}

WORKDIR ${APP_PATH}
