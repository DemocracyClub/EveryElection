#!/bin/sh
set -x
cd /var/www/every_election/repo
#### BEGIN CONFIGURATION ####
./serverscripts/setenv.sh .env

# set dates for backup rotation
NOWDATE=`date +%Y-%m-%d-%H`
DAY_OF_MONTH=`date +%d`
EXPIRE=true


# set backup directory variables
DESTDIR='every_election'
SHORT_TERM_BUCKET='dc-ee-production-database-backups'
#### END CONFIGURATION ####

BACKUP_PG_DUMP_CONNECTION_STRING="-d every_election -H $EE_DATABASE_HOST -Fc"

if  [ $DAY_OF_MONTH = 01 ] ;
then
  pg_dump $BACKUP_PG_DUMP_CONNECTION_STRING | aws s3 cp - \
    s3://$SHORT_TERM_BUCKET/$DESTDIR/$NOWDATE-backup.dump \
    --storage-class=STANDARD_IA

else
  pg_dump $BACKUP_PG_DUMP_CONNECTION_STRING | aws s3 cp - \
    s3://$SHORT_TERM_BUCKET/$DESTDIR/$NOWDATE-backup.dump \
    --storage-class=STANDARD_IA \
    --expires "$(date -I -d '60 days')"
fi
