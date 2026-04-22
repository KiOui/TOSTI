#!/bin/sh

# Set ownership
chown -R nobody:nogroup /app/cache

echo "🔍 Checking database connection..."
python manage.py check --database=default

echo "📊 Checking migration status..."
python manage.py showmigrations --plan | grep constance || echo "No constance migrations found"

echo "🚀 Running migrations..."
python manage.py migrate --noinput

echo "🌐 Starting uWSGI server..."
uwsgi --http :80 --wsgi-file /app/tosti/wsgi.py --master --processes 4 --threads 2 --uid nobody --gid nogroup --disable-logging --static-map ${DJANGO_STATIC_URL}=${DJANGO_STATIC_ROOT} --static-map ${DJANGO_MEDIA_URL}=${DJANGO_MEDIA_ROOT}