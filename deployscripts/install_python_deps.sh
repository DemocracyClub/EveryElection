#!/usr/bin/env bash
set -xeE

# should we delete the env and recreate?
cd /var/www/every_election/repo/
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements/production.txt
pip install gevent