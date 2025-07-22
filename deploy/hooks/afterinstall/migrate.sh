#!/bin/bash
set -euxo pipefail

cd /var/www/every_election/repo/
uv run manage.py migrate --noinput
