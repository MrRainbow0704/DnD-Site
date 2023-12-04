from pathlib import Path
from dotenv import load_dotenv
from os import getenv


# Main dir path
ROOT_PATH = Path(__file__).resolve().parent

# Secrets from .env
if load_dotenv():
    SECRET_KEY = getenv("SECRET_KEY")
    PEPPER = getenv("PEPPER")
    DB_HOST_NAME = getenv("HOST_NAME")
    DB_HOST_PORT = int(getenv("HOST_PORT"))
    DB_USER_NAME = getenv("USER_NAME")
    DB_USER_PASSWORD = getenv("USER_PASSWORD")
else:
    print("Error loading .env")