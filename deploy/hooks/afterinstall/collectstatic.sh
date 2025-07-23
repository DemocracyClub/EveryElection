#!/usr/bin/env bash
set -xeE


cd /var/www/every_election/code/
. .venv/bin/activate
python manage.py collectstatic --noinput --clear
