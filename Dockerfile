FROM python:3.9-slim-buster

ARG POETRY_EXPORT
ARG PROJECT_ID
ARG SENTRY_DSN

ENV PROJECT_ID $PROJECT_ID
ENV SENTRY_DSN $SENTRY_DSN

ADD quant_tick /quant_tick/
ADD main.py /

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --no-cache-dir $POETRY_EXPORT \
    && apt-get purge -y --auto-remove build-essential \
    && apt-get clean  \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/main.py"]
