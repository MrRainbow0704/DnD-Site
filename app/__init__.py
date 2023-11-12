from flask import Flask
from pathlib import Path
from dotenv import load_dotenv
from os import getenv

ROOT_PATH = Path(__name__).resolve().parent
app = Flask(__name__, root_path=ROOT_PATH)
app.secret_key = getenv("SECRET_KEY")
MainDb = "db/Main.sqlite3"


from . import routes
from .api import bp as api_bp

app.register_blueprint(api_bp, url_prefix="/api")

from .api import functions

functions.start_database(
    MainDb,
    """CREATE TABLE IF NOT EXISTS Users (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            UserName TEXT UNIQUE NOT NULL,
            Pwd TEXT NOT NULL,
            Campaigns TEXT DEFAULT '[]')
            """,
)
functions.start_database(
    MainDb,
    """CREATE TABLE IF NOT EXISTS Campaigns (
            Code INTEGER PRIMARY KEY,
            DungeonMaster INTEGER UNIQUE NOT NULL,
            Players TEXT DEFAULT '[]')
            """,
)
