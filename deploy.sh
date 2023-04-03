#!/usr/bin/env bash

cd "${0%/*}" || exit
ssh-agent bash -c 'ssh-add .ssh/id_ed25519; git pull'
source env/bin/activate
website/manage.py migrate
website/manage.py collectstatic --noinput
touch RELOAD
