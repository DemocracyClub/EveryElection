#!/bin/bash
set -euxo pipefail

cd /var/www/every_election/repo/
source .venv/bin/activate
python manage.py migrate --noinput