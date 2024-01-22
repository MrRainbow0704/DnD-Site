"""Il modulo che contiene l'applicazione principale."""

from flask import Flask
import config
from time import sleep
from . import functions

# Crea l'applicazione e imposta la secret key
app = Flask(__name__, root_path=config.ROOT_PATH)
app.secret_key = config.SECRET_KEY
app.config["UPLOAD_FOLDER"] = config.UPLOADS_PATH

# Prova a connettersi al database principale per 10 volte, esci dal programma in caso di fallimento
tentativi, tentativi_max = 0, 10
while tentativi < tentativi_max:
    sleep(1)
    MAINDB = functions.create_db(
        config.DB_HOST_NAME,
        config.DB_HOST_PORT,
        config.DB_USER_NAME,
        config.DB_USER_PASSWORD,
        "dnd_site_main",
    )
    if MAINDB == False:
        tentativi += 1
        print(
            f"Failed to connect to the database {config.DB_USER_NAME}@{config.DB_HOST_NAME}:{config.DB_HOST_PORT}"
        )
    else:
        break
else:
    quit("Database connection failure. (MainDB)")


from . import routes
from .api import bp as api_bp

# Registra la blueprint per API
app.register_blueprint(api_bp, url_prefix="/api")

# Crea le tabelle `Users` e `Campaigns` dentro il database principale
functions.SQL_query(
    MAINDB,
    """CREATE TABLE IF NOT EXISTS Users (
            Id INTEGER PRIMARY KEY AUTO_INCREMENT,
            UserName VARCHAR(32) UNIQUE NOT NULL,
            Pwd VARCHAR(512) NOT NULL,
            Salt VARCHAR(32) NOT NULL,
            Campaigns TEXT NOT NULL DEFAULT ('[]'));
            """,
)

functions.SQL_query(
    MAINDB,
    """CREATE TABLE IF NOT EXISTS Campaigns (
            Code VARCHAR(32) PRIMARY KEY,
            CampaignName TEXT NOT NULL,
            DungeonMaster INTEGER NOT NULL,
            Players TEXT NOT NULL DEFAULT ('[]'));
            """,
)
