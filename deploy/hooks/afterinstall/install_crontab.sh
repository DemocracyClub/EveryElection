cd /var/www/every_election/repo/
mv deploy/crontab /etc/cron.d/every_election_cron
chown root:root /etc/cron.d/every_election_cron
chmod 755 /etc/cron.d/every_election_cron
