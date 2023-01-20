#!/bin/bash
set -e
set -x

# Drop and re-create the local DB
dropdb every_election
createdb every_election

# Pipe the latest backup into the local DB
LATEST_FILE=`aws s3 ls s3://dc-ee-production-database-backups/every_election/ | sort | tail -n 1 | rev | cut -d' ' -f 1 | rev`
aws s3 cp s3://dc-ee-production-database-backups/every_election/$LATEST_FILE - | pg_restore -d every_election --if-exists --clean

# Because our local code might have migrated the database, run migrations
cd /var/www/every_election/repo/
source .venv/bin/activate
python manage.py migrate --noinput
