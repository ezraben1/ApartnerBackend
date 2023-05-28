from .common import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "2fzk-hx1$ckm2s2epw^t^i5h1prdqy9#v(-(y%vequol()-^&_"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "apartnerprod",
        "HOST": "localhost",
        "USER": "root",
        "PASSWORD": "123456",
    }
}
# dev server
cloudinary.config(
    cloud_name=("dnis06cto"),
    api_key=("419768594117284"),
    api_secret=("zexmum1c5fbT8-959jXEb1VQj2w"),
)
# ALLOWED_HOSTS = ["7c53-77-125-161-21.ngrok-free.app", "http://localhost:3000/"]
