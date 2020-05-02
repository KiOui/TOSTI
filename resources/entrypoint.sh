#!/usr/bin/env bash

set -e

until pg_isready --host="${POSTGRES_HOST}" --username="${POSTGRES_USER}" --quiet; do
    sleep 1;
done

touch -a /tosti/log/uwsgi.log
touch -a /tosti/log/django.log

cd /tosti/src/website

./manage.py collectstatic --no-input -v0 --ignore="*.scss"
./manage.py migrate --no-input

chown --recursive www-data:www-data /tosti/

echo "Starting uwsgi server."
uwsgi --chdir=/tosti/src/website \
    --module=website.wsgi:application \
    --master --pidfile=/tmp/project-master.pid \
    --socket=:8000 \
    --processes=5 \
    --uid=www-data --gid=www-data \
    --harakiri=20 \
    --post-buffering=16384 \
    --max-requests=5000 \
    --thunder-lock \
    --vacuum \
    --logfile-chown \
    --logto2=/tosti/log/uwsgi.log \
    --ignore-sigpipe \
    --ignore-write-errors \
    --disable-write-exception
