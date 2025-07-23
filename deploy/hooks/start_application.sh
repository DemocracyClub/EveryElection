#!/usr/bin/env bash
set -xeE

# Ensure gunicorn is on the right port
sudo sed "s/127.0.0.1/0.0.0.0/g" /etc/systemd/system/every_election_gunicorn.service -i
sudo systemctl daemon-reload

# enabling will allow the services to start if the instance reboots
systemctl enable every_election_gunicorn.service
systemctl start every_election_gunicorn.service
