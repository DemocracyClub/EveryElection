# Installation
EveryElection requires Python 3.x and Postgres.

## Install Python dependencies

Every Election uses [uv](https://docs.astral.sh/uv/) to manage python packages.
[Install uv](https://docs.astral.sh/uv/getting-started/installation/) first if you don't already have it. Then

```
uv sync
```

Gotcha: If you're having trouble installing psycopg2-binary on Apple silicon, set your library path before retrying the install:
```commandline
export LIBRARY_PATH=$LIBRARY_PATH:/opt/homebrew/opt/openssl/lib
```

## Install JS Packages

```
npm ci
```

## Install Tippecanoe

Every Election uses tippecanoe to generate pmtiles. Compiling tippecanoe requires the following dependencies:

```
sudo apt install gcc g++ make libsqlite3-dev zlib1g-dev
```

Once you've installed those dependencies, follow tippecanoe's install instructions [here](https://github.com/felt/tippecanoe).

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

Create your local settings file:
```
cp .env.example .env
```

In this file, add your database username and password.


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
This project uses pytest and playwright.

Before running tests you'll need to run `playwright install`.

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

This project uses [ruff](https://beta.ruff.rs/docs/) and [djhtml](https://github.com/rtts/djhtml) for linting and formatting. You can run them with:

    ruff check .
    ruff format .
    git ls-files '*.html' | xargs djhtml

ruff has in-built functionality to fix common linting errors. Use the `--fix` option to do this.

## Development Notes

- If adding any new fields to EveryElection, you may also need to add them to the EE API app within this project.
