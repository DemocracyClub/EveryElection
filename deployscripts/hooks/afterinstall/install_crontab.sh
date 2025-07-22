cd /var/www/every_election/repo/
mv deployscripts/crontab /etc/cron.d/every_election_cron
chown root:root /etc/cron.d/every_election_cron
chmod 755 /etc/cron.d/every_election_cron
