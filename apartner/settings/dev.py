from .common import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-406_2can@1@=mpv&wtm5*00vfg3i3x6pi61nv5ab)2fv4o$c!i"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "apartner",
        "HOST": "localhost",
        "USER": "root",
        "PASSWORD": "123456",
    }
}
