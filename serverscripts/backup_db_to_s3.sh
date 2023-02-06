#!/bin/bash
set -x
cd /var/www/every_election/repo
#### BEGIN CONFIGURATION ####
source .env

# set backup directory variables
DESTDIR='every_election'
SHORT_TERM_BUCKET='dc-ee-production-database-backups'
#### END CONFIGURATION ####

BACKUP_PG_DUMP_CONNECTION_STRING="-d every_election -h $EE_DATABASE_HOST -Fc"
export PGPASSWORD=$EE_DATABASE_PASSWORD
pg_dump $BACKUP_PG_DUMP_CONNECTION_STRING > /tmp/ee-backup.dump

aws s3 cp \
  /tmp/ee-backup.dump \
  s3://$SHORT_TERM_BUCKET/$DESTDIR/$NOWDATE-backup.dump \
  --storage-class=STANDARD_IA

rm /tmp/ee-backup.dump
