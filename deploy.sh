#!/usr/bin/env bash

cd "${0%/*}" || exit
git pull
source env/bin/activate
website/manage.py migrate
website/manage.py collectstatic --noinput
touch RELOAD
