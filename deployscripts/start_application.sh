#!/usr/bin/env bash
set -xeE

# Ensure gunicorn is on the right port
sudo sed "s/127.0.0.1/0.0.0.0/g" /etc/systemd/system/gunicorn_every_election.service -i
sudo systemctl daemon-reload

# enabling will allow the services to start if the instance reboots
systemctl enable gunicorn_every_election.service
systemctl start gunicorn_every_election.service
