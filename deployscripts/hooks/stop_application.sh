#!/usr/bin/env bash
set -xeE

service gunicorn_every_election stop

# delete all code including hidden files
rm -rf /var/www/every_election/repo/* /var/www/every_election/repo/.* 2> /dev/null || true
