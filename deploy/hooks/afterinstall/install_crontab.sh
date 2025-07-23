#!/usr/bin/env bash
set -xeE

cd /var/www/every_election/code/
mv deploy/files/conf/crontab /etc/cron.d/every_election_cron
chown root:root /etc/cron.d/every_election_cron
chmod 755 /etc/cron.d/every_election_cron
