#!/usr/bin/env bash
set -xeE


cd /var/www/every_election/repo/
. .venv/bin/activate
python manage.py collectstatic --noinput --clear
