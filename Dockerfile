FROM python:3.8
MAINTAINER Tartarus

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE tosti.settings.production
ENV PATH /root/.poetry/bin:${PATH}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /tosti/src
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY poetry.lock pyproject.toml /tosti/src/

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends postgresql-client && \
    rm --recursive --force /var/lib/apt/lists/* && \
    \
    mkdir --parents /tosti/src/ && \
    mkdir --parents /tosti/log/ && \
    mkdir --parents /tosti/static/ && \
    chmod +x /usr/local/bin/entrypoint.sh && \
    \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python && \
    poetry config --no-interaction --no-ansi virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-dev


COPY website /tosti/src/website/