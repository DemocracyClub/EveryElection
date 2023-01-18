#!/bin/bash
set -e
set -x

cd /var/www/every_election/repo/
source .venv/bin/activate
python manage.py add_tags \
    -u "https://ons-cache.s3.eu-west-1.amazonaws.com/NUTS_Level_1_(January_2018)_Boundaries.geojson" \
    --fields ''{"NUTS118NM": "value", "NUTS118CD": "key"}'' \
    --tag-name NUTS1
