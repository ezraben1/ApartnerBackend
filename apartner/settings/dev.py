from .common import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "2fzk-hx1$ckm2s2epw^t^i5h1prdqy9#v(-(y%vequol()-^&_"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "apartner",
        "HOST": "localhost",
        "USER": "root",
        "PASSWORD": "123456",
    }
}
