# Installation
EveryElection requires Python 3.x and Postgres.

## Install Python dependencies

```
pip install -U pip
pip install -r requirements.txt
pip install -r requirements/local.txt
```
Gotcha: If you're having trouble installing psycopg2-binary on Apple silicon, set your library path before retrying the install:
```commandline
export LIBRARY_PATH=$LIBRARY_PATH:/opt/homebrew/opt/openssl/lib
```

## Set up database
By default, EveryElection uses PostgreSQL with the PostGIS extension. 
To set this up locally, first install the packages:
```
sudo apt-get install postgresql postgis

# MacOS
brew install postgresql postgis
```

Create the database:
```
sudo -u postgres createdb every_election

# MacOS
createdb every_election
```

Finally, add the postgis extension to the database:
```
sudo -u postgres psql -d every_election -c "CREATE EXTENSION postgis;"

# MacOS
psql -d every_election -c "CREATE EXTENSION postgis;"
```

Create your local.py settings file:
```
cp every_election/settings/local.example.py every_election/settings/local.py
```

In this file, add your database credentials to the `DATABASES` dict.


To populate the database from a dumpfile, run: 

```
pg_restore -d every_election -C backup.dump
```

If you have a DC AWS account, you can grab the latest production db backup like so:
```
export AWS_PROFILE=dev-ee-dc #  you may need to configure this profile
# Drop and re-create the local DB
dropdb every_election
createdb every_election

# Pipe the latest backup into the local DB
LATEST_FILE=`aws s3 ls s3://dc-ee-production-database-backups/every_election/ | sort | tail -n 1 | rev | cut -d' ' -f 1 | rev`
aws s3 cp s3://dc-ee-production-database-backups/every_election/$LATEST_FILE - | pg_restore -d every_election --if-exists --clean
```
_We strongly advise you to create a local backup before dropping your database!_

## Run the tests
This project uses pytest. 

To run the full suite, run:
```commandline
pytest
```
_Unless indicated by GitHub issues, you should expect all tests to pass after following the steps outlined above._

## Try it out
To bring the project up, run:
```commandline
python manage.py runserver
```
You should then be able to access the project via your browser. 

It is recommended to attempt to add an election ID 
to verify that the install was a success.

## Formatting
This project is [Black](https://black.readthedocs.io/en/stable/) formatted. 
To format a specific file, run:
```commandline
black path/your_file.py
```
To run a project-wide reformat, run:
```commandline
black .

```

Additionally, this project uses [ruff](https://beta.ruff.rs/docs/) for linting. You can run it with:

    ruff . 

ruff has in-built functionality to fix common linting errors. Use the `--fix` option to do this.

Both Black and ruff are both automatically called as part of pytest in this project.

## Development Notes

- If adding any new fields to EveryElection, you may also need to add them to the EE API app within this project.


