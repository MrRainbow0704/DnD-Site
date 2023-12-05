from pathlib import Path
from dotenv import load_dotenv
from os import getenv


# Main dir path
ROOT_PATH = Path(__file__).resolve().parent

# Secrets from .env
if load_dotenv():
    SECRET_KEY = getenv("SECRET_KEY")
    PEPPER = getenv("PEPPER")
    HOST = getenv("HOST")
    PORT = int(getenv("PORT"))
    DEBUG = bool(int(getenv("DEBUG")))
    DB_HOST_NAME = getenv("DB_HOST_NAME")
    DB_HOST_PORT = int(getenv("DB_HOST_PORT"))
    DB_USER_NAME = getenv("DB_USER_NAME")
    DB_USER_PASSWORD = getenv("DB_USER_PASSWORD")
else:
    print("Error loading .env")
