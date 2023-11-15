from flask import Flask
from pathlib import Path
from dotenv import load_dotenv
from os import getenv
from . import functions

ROOT_PATH = Path(__name__).resolve().parent
app = Flask(__name__, root_path=ROOT_PATH)
app.secret_key = getenv("SECRET_KEY")
DbHostName = getenv("HOST_NAME")
DbUserName = getenv("USER_NAME")
DbUserPassword = getenv("USER_PASSWORD")
MainDb = functions.create_db(
    DbHostName,
    DbUserName,
    DbUserPassword,
    "dnd_site_main",
)


from . import routes
from .api import bp as api_bp

app.register_blueprint(api_bp, url_prefix="/api")


functions.SQL_query(
    MainDb,
    """CREATE TABLE IF NOT EXISTS Users (
            Id INTEGER PRIMARY KEY AUTO_INCREMENT,
            UserName TEXT UNIQUE NOT NULL,
            Pwd TEXT NOT NULL,
            Campaigns TEXT DEFAULT '[]');
            """,
)
functions.SQL_query(
    MainDb,
    """CREATE TABLE IF NOT EXISTS Campaigns (
            Code INTEGER PRIMARY KEY,
            DungeonMaster INTEGER UNIQUE NOT NULL,
            Players TEXT DEFAULT '[]');
            """,
)
