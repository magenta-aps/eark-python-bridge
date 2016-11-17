# -*- coding: utf-8 -*-
import os

# Add settings here

# Paths
BASE_DIR = os.path.dirname(  # eark-python-bridge
    os.path.realpath(__file__)  # this script
)
APPLICATION_ROOT = BASE_DIR
DATA_DIR = BASE_DIR + '/data/'
PREVIEW_DIR = BASE_DIR + '/preview/'

# Database
#SQLALCHEMY_DATABASE_URI = 'sqlite:///%s/data.db' % BASE_DIR
SQLALCHEMY_DATABASE_URI = 'mysql://eark:eark@localhost/eark_ipViewer'
SQLALCHEMY_TRACK_MODIFICATIONS = False

DEBUG = True
HOST = '0.0.0.0'
PORT = 8889
