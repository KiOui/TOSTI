#/bin/sh

cd "${0%/*}"
git pull
source env/bin/activate
website/manage.py migrate
website/manage.py collectstatic --noinput
touch RELOAD
