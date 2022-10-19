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

