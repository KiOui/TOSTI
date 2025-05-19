#!/bin/sh

export > /etc/env_vars.sh

chown -R nobody:nogroup /app/cache

# Create the cron job but have it run as the nobody user
echo "*/1 * * * * nobody . /etc/env_vars.sh && /usr/local/bin/python /app/manage.py runcrons --silent >> /var/log/cron.log 2>&1" > /etc/cron.d/cron-schedule
chmod 0644 /etc/cron.d/cron-schedule
crontab /etc/cron.d/cron-schedule
touch /var/log/cron.log
chmod 666 /var/log/cron.log

# Start cron in the background
cron

# Tail the cron log to keep the container running
tail -f /var/log/cron.log
