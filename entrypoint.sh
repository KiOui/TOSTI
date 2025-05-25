#!/bin/sh

# Set ownership
chown -R nobody:nogroup /app/cache

echo "🔍 Checking database connection..."
python manage.py check --database=default

echo "📊 Checking migration status..."
python manage.py showmigrations --plan | grep constance || echo "No constance migrations found"

echo "🚀 Running migrations..."
python manage.py migrate --noinput

echo "🔧 Ensuring constance table exists..."
# Create constance table if it doesn't exist
python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS constance_constance (
            id SERIAL PRIMARY KEY,
            key VARCHAR(255) NOT NULL UNIQUE,
            value TEXT NOT NULL
        );
    ''')
print('Constance table ensured')
" || echo "Failed to ensure constance table, continuing..."

echo "📝 Setting up SAML certificates..."
echo "${SAML_PUBLIC_KEY_FILE}" > /app/tosti/saml/public.cert
echo "${SAML_PRIVATE_KEY_FILE}" > /app/tosti/saml/private.key

echo "🌐 Starting uWSGI server..."
uwsgi --http :80 --wsgi-file /app/tosti/wsgi.py --master --processes 4 --threads 2 --uid nobody --gid nogroup --disable-logging --static-map ${DJANGO_STATIC_URL}=${DJANGO_STATIC_ROOT} --static-map ${DJANGO_MEDIA_URL}=${DJANGO_MEDIA_ROOT}