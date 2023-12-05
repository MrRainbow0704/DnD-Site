"""Il modulo che contiene l'applicazione principale."""

from flask import Flask
import config
from . import functions

# Crea l'applicazione e inposta la secret key
app = Flask(__name__, root_path=config.ROOT_PATH)
app.secret_key = config.SECRET_KEY

# Inizializza la connessione al database principale, esci dal programma in caso di fallimento
MAINDB = functions.create_db(
    config.DB_HOST_NAME,
    config.DB_HOST_PORT,
    config.DB_USER_NAME,
    config.DB_USER_PASSWORD,
    "dnd_site_main",
)
if MAINDB == False:
    quit("Database connection faliure. (MainDB)")


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
