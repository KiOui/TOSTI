FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev python3-dev cron python3-pip xmlsec1 python3-dev libssl-dev libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file to leverage Docker cache
COPY pyproject.toml poetry.lock /app/

# Install project dependencies
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --with prod --no-interaction --no-ansi

# Copy the current directory contents into the container at /app
COPY website /app
COPY entrypoint.sh /
COPY entrypoint_cron.sh /

ENV DJANGO_SETTINGS_MODULE tosti.settings.production

ENV DJANGO_STATIC_ROOT /static
ENV DJANGO_MEDIA_ROOT /media

RUN mkdir -p $DJANGO_STATIC_ROOT
RUN mkdir -p $DJANGO_MEDIA_ROOT

ENV DJANGO_STATIC_URL /static/
ENV DJANGO_MEDIA_URL /media/

RUN touch /var/log/django.log
RUN mkdir -p /app/cache

RUN python manage.py collectstatic --noinput

RUN chown -R nobody:nogroup $DJANGO_MEDIA_ROOT
RUN chown -R nobody:nogroup /var/log/django.log
RUN chown -R nobody:nogroup /app/cache

RUN mkdir -p /app/tosti/saml

EXPOSE 80

# Command to run uWSGI
CMD ["/bin/sh", "/entrypoint.sh"]