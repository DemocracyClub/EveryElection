#!/usr/bin/env bash
set -xeE

# enabling will allow the services to start if the instance reboots
systemctl enable gunicorn_every_election.service

systemctl start gunicorn_every_election.service
