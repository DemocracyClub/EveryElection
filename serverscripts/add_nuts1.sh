#!/bin/bash
set -e
set -x

cd /var/www/every_election/repo/
source .venv/bin/activate
python manage.py add_tags \
    -u "https://s3.eu-west-2.amazonaws.com/ee.public.data/ons-cache/NUTS_Level_1_(January_2018)_Boundaries.gpkg" \
    --fields '{"NUTS118NM": "value", "NUTS118CD": "key"}' \
    --tag-name NUTS1
