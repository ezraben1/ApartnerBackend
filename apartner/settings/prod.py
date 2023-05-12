# prod.py
import os
from .common import *
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".herokuapp.com",
    "apartnerbackend.herokuapp.com",
    "http://localhost:3000",
]

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("JAWSDB_URL"), conn_max_age=600
    )
}
