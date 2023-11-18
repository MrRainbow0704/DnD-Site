from flask import Flask
from pathlib import Path
from dotenv import load_dotenv
from os import getenv
from . import functions

ROOT_PATH = Path(__name__).resolve().parent
app = Flask(__name__, root_path=ROOT_PATH)
app.secret_key = getenv("SECRET_KEY")
PEPPER = getenv("PEPPER")
DBHOSTNAME = getenv("HOST_NAME")
DBUSERNAME = getenv("USER_NAME")
DBUSERPASSWORD = getenv("USER_PASSWORD")
MAINDB = functions.create_db(
    DBHOSTNAME,
    DBUSERNAME,
    DBUSERPASSWORD,
    "dnd_site_main",
)


from . import routes
from .api import bp as api_bp

app.register_blueprint(api_bp, url_prefix="/api")


functions.SQL_query(
    MAINDB,
    """CREATE TABLE IF NOT EXISTS Users (
            Id INTEGER PRIMARY KEY AUTO_INCREMENT,
            UserName VARCHAR(32) UNIQUE NOT NULL,
            Pwd VARCHAR(512) NOT NULL,
            Campaigns TEXT DEFAULT '[]');
            """,
)
functions.SQL_query(
    MAINDB,
    """CREATE TABLE IF NOT EXISTS Campaigns (
            Code VARCHAR(32) PRIMARY KEY,
            CampaignName TEXT NOT NULL,
            DungeonMaster INTEGER NOT NULL,
            Players TEXT DEFAULT '[]');
            """,
)
