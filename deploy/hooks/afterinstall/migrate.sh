#!/bin/bash
set -euxo pipefail

cd /var/www/every_election/code/
uv run manage.py migrate --noinput
