import os
import secrets

is_development = os.environ.get('SERVER_SOFTWARE', 'Dev').startswith('Dev')

DEBUG = True
SECRET_KEY = "5oZW6$#^#3w3FE3"

if not is_development:
    DEBUG = False
    SECRET_KEY = secrets.SECRET_KEY
