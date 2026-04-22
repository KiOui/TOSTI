FROM python:3.14-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev python3-dev cron python3-pip xmlsec1 python3-dev libssl-dev libsasl2-dev curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"
ENV UV_NO_DEV=1

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file to leverage Docker cache
COPY pyproject.toml uv.lock /app/

# Install dependencies
RUN uv sync --locked --group prod

# Copy the current directory contents into the container at /app
COPY website /app
COPY entrypoint.sh /
COPY entrypoint_cron.sh /

ENV DJANGO_SETTINGS_MODULE="tosti.settings.production"

ENV DJANGO_STATIC_ROOT="/static"
ENV DJANGO_MEDIA_ROOT="/media"

RUN mkdir -p $DJANGO_STATIC_ROOT
RUN mkdir -p $DJANGO_MEDIA_ROOT

ENV DJANGO_STATIC_URL="/static/"
ENV DJANGO_MEDIA_URL="/media/"

RUN touch /var/log/django.log
RUN mkdir -p /app/cache

RUN uv run manage.py collectstatic --noinput

RUN chown -R nobody:nogroup $DJANGO_MEDIA_ROOT
RUN chown -R nobody:nogroup /var/log/django.log
RUN chown -R nobody:nogroup /app/cache

RUN mkdir -p /app/tosti/saml

EXPOSE 80

# Command to run uWSGI
CMD ["/bin/sh", "/entrypoint.sh"]