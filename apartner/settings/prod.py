# prod.py
import os
from .common import *
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".herokuapp.com",
    "apartnerbackend.herokuapp.com",
    "http://localhost:3000",
    "https://ecac-77-125-161-21.ngrok-free.app",
]

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("JAWSDB_URL"), conn_max_age=600
    )
}


cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
)
