#!/usr/bin/env bash

#
# Installation script for eark-python-bridge.
# -------------------------------------------
#
# This script installs dependencies, 
# initializes virtualenv, the database and 
# creates directories needed by the application.
#

PYTHON_ENV="python-env"
DATABASE_FILE="data.db"

sudo apt-get -y install python-pip python-dev build-essential sqlite3
sudo pip install virtualenv
sudo pip install --upgrade pip

# Initialize virtualenv
virtualenv $PYTHON_ENV
source python-env/bin/activate
pip install -r requirements.txt

# Initialize sqlite3 database
# HACK: There's apparently no other way to create an empty sqlite3 db...!
sqlite3 $DATABASE_FILE ".databases"
# HACK END
python init_db.py
deactivate # Step out of virtualenv

# Make directories
mkdir data preview
