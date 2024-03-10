#!/bin/sh
python manage.py migrate --noinput
echo "${SAML_PUBLIC_KEY_FILE}" >> /app/tosti/saml/public.cert
echo "${SAML_PRIVATE_KEY_FILE}" >> /app/tosti/saml/private.key
echo "${SAML_METADATA_FILE}" | base64 -d >> /app/tosti/saml/metadata.xml
uwsgi --http :80 --wsgi-file /app/tosti/wsgi.py --master --processes 4 --threads 2 --uid nobody --gid nogroup --disable-logging --static-map ${DJANGO_STATIC_URL}=${DJANGO_STATIC_ROOT} --static-map ${DJANGO_MEDIA_URL}=${DJANGO_MEDIA_ROOT}