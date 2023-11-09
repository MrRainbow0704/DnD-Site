from flask import Flask
from pathlib import Path

ROOT_PATH = Path(__name__).resolve().parent
app = Flask(__name__, root_path=ROOT_PATH)
UserDb = "db/User.sqlite3"


from . import routes
from .api import bp as api_bp

app.register_blueprint(api_bp, url_prefix="/api")

from .api import functions
functions.start_database(
    UserDb,
    """CREATE TABLE IF NOT EXISTS Users (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            UserName TEXT NOT NULL,
            Pwd TEXT NOT NULL,
            Campaign TEXT)
            """,
)
