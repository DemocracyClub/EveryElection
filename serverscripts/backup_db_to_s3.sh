#!/bin/sh
set -x

#### BEGIN CONFIGURATION ####

# set dates for backup rotation
NOWDATE=`date +%Y-%m-%d-%H`
DAY_OF_MONTH=`date +%d`
EXPIRE=true


# set backup directory variables
DESTDIR='every_election'
SHORT_TERM_BUCKET='dc-ee-short-term-backups'
#### END CONFIGURATION ####


if  [ $DAY_OF_MONTH = 01 ] ;
then
  pg_dump -d $BACKUP_PG_DUMP_CONNECTION_STRING -Fc | aws s3 cp - \
    s3://$SHORT_TERM_BUCKET/$DESTDIR/$NOWDATE-backup.dump \
    --storage-class=STANDARD_IA

else
  pg_dump -d $BACKUP_PG_DUMP_CONNECTION_STRING -Fc | aws s3 cp - \
    s3://$SHORT_TERM_BUCKET/$DESTDIR/$NOWDATE-backup.dump \
    --storage-class=STANDARD_IA \
    --expires "$(date -I -d '60 days')"
fi
