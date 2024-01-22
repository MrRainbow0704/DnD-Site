"""Un modulo che contiene delle funzioni utili utilizzate dall'API"""

from flask import session, url_for
from typing import Any, Literal
import re as regex
import json
from uuid import uuid4 as uuid
import mysql.connector as mysql
import hashlib
import config
from .. import functions


def empty_input(*args: Any) -> bool:
    """Controlla che nessuno degli argomenti sia nullo o vuoto.

    Args:
        *args (Any): Argomenti da passare alla funzione
    Returns:
        bool: Se il valore è vuoto o no.
    """

    # Controlla per ogni elemento se è vuoto
    for i in args:
        if not bool(i) and type(i) != int:
            return True
    return False


def invalid_name(name: str) -> bool:
    """Controlla se il nome è valido.

    Args:
        name (str): Nome da controllare.

    Returns:
        bool: Se il nome è valido o no.
    """

    # Controlla se il nome contiene solo lettere, numeri o _
    # e se ha una lunghezza tra i 4 e i 32 caratteri
    if not regex.match(r"^[a-zA-Z0-9_]{4,32}$", name):
        return True
    return False


def create_user(db: mysql.MySQLConnection, name: str, pwd: str, salt: str) -> bool:
    """Crea un utente nel database criptandone la password.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        name (str): Nome dell'utente.
        pwd (str): Password dell'utente (in chiaro).

    Returns:
        bool: Se la funzione ha funzionato correttamente.
    """

    # Cripta la password
    hashedPwd = hash_password(pwd, salt)

    # Inserisce i dati all'interno del database nella tabella `Users` e controlla se va a buon fine
    if (
        functions.SQL_query(
            db,
            "INSERT INTO Users (UserName, Pwd, Salt) VALUES (%s, %s, %s);",
            (name, hashedPwd, salt),
        )
        == False
    ):
        return False
    else:
        return True


def login_user(db: mysql.MySQLConnection, name: str, pwd: str) -> bool:
    """Esegue il login di un utente.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        name (str): Nome dell'utente.
        pwd (str): Password dell'utente (in chiaro).

    Returns:
        bool: Se l'operazione è andata a buon fine o no.
    """

    # Ottieni il profilo dell'utente attraverso il nume
    getNameResult = functions.get_user_from_name(db, name)

    # Controlla che l'utente esista
    if not getNameResult:
        return False

    # Cripta la password inserita e confrontala con quella presente nel database
    pwdHashed = getNameResult["Pwd"]
    salt = getNameResult["Salt"]
    if not verify_password(pwd, salt, pwdHashed):
        return False

    # Se tutto va a buon fine, inizia una muova sessione
    session["Id"] = getNameResult["Id"]
    session["UserName"] = getNameResult["UserName"]
    return True


def hash_password(password: str, salt: str) -> str:
    """Cripta una password.

    Args:
        password (str): Password (in chiaro).

    Returns:
        str: Password (criptata).
    """

    # Cripta la password usando sha512
    return hashlib.sha512(str(salt + password + config.PEPPER).encode()).hexdigest()


def verify_password(inputPwd: str, salt: str, hashedPwd: str) -> bool:
    """Verifica che le password corrispondano.

    Args:
        inputPwd (str): Password da controllare (in chiaro).
        hashedPwd (str): Password originale (criptata).

    Returns:
        bool: Se le password corrispondono o no.
    """

    # Verifica che le password corrispondano confrontandone gli hash
    return hash_password(inputPwd, salt) == hashedPwd


def create_campaign(
    db: mysql.MySQLConnection, c_name: str, dm_id: int
) -> str | Literal[False]:
    """Crea una nuova campagna.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        c_name (str): Nome della campagna.
        dm_id (int): L'id del dungeon master.

    Returns:
        str | Literal[False]: Il codice della nuova campagna.
    """

    code = uuid().hex
    if (
        functions.SQL_query(
            db,
            "INSERT INTO Campaigns (Code, CampaignName, DungeonMaster) VALUES (%s, %s, %s);",
            (code, c_name, dm_id),
        )
        == False
    ):
        return False

    CampaignDb = functions.create_db(
        config.DB_HOST_NAME,
        config.DB_HOST_PORT,
        config.DB_USER_NAME,
        config.DB_USER_PASSWORD,
        f"dnd_site_campaign_{code}",
    )
    if CampaignDb == False:
        return False

    if (
        functions.SQL_query(
            CampaignDb,
            """CREATE TABLE IF NOT EXISTS Players (
                UserId INTEGER PRIMARY KEY,
                Name TEXT UNIQUE NOT NULL,
                DmgTaken INTEGER DEFAULT 0,
                Lvl INTEGER DEFAULT 1,
                Exp INTEGER DEFAULT 0,
                Inventory TEXT DEFAULT ('[]'),
                Class TEXT DEFAULT ('{}'),
                Race TEXT DEFAULT ('{}'),
                Equipment TEXT DEFAULT ('{}'),
                Stats TEXT DEFAULT ('{}')
                );
        """,
        )
        == False
    ):
        return False
    return code


def get_campaign_players(
    db: mysql.MySQLConnection, code: str
) -> list[dict] | Literal[False]:
    """Restituisce tutti i giocatori di una campagna.

    Args:
        db (mysql.MySQLConnection): Una connessione a un database.
        code (str): Il codice della campagna.

    Returns:
        Literal[False] | list[dict]: La lista di giocatori.
    """

    CampaignDb = functions.db_connect(
        config.DB_HOST_NAME,
        config.DB_HOST_PORT,
        config.DB_USER_NAME,
        config.DB_USER_PASSWORD,
        f"dnd_site_campaign_{code}",
    )
    if CampaignDb == False:
        return False

    players = functions.SQL_query(CampaignDb, "SELECT * FROM Players;")
    if players == False:
        return False
    return players


def add_campaign(db: mysql.MySQLConnection, code: str, name: str, id_: int) -> bool:
    """Aggiunge una campagna alla lista di campagne di un utente.

    Args:
        db (mysql.MySQLConnection): Una connessione a un database.
        code (str): Il codice della campagna da aggiungere.
        name (str): Il nome della campagna da aggiungere.
        id_ (int): L'id dell'utente a cui aggiungere la campagna.

    Returns:
        bool: True se tutto va a buon fine, altrimenti False.
    """

    campaigns = functions.get_user_campaigns(db, id_)
    campaigns.append(
        {"href": url_for("campaign", code=code), "code": code, "name": name}
    )

    if (
        functions.SQL_query(
            db,
            "UPDATE Users SET Campaigns = %s WHERE id = %s;",
            (
                json.dumps(campaigns),
                id_,
            ),
        )
        == False
    ):
        return False
    return True


def remove_campaign(db: mysql.MySQLConnection, code: str, id_: int) -> bool:
    """Rimuove una campagna alla lista di campagne di un utente.

    Args:
        db (mysql.MySQLConnection): Una connessione a un database.
        code (str): Il codice della campagna da rimuovere.
        id_ (int): L'id dell'utente a cui rimuovere la campagna.

    Returns:
        bool: True se tutto va a buon fine, altrimenti False.
    """

    campaigns = functions.get_user_campaigns(db, id_)
    if campaigns == False:
        return False
    for c in campaigns:
        if c["code"] == code:
            campaigns.remove(c)
    if (
        functions.SQL_query(
            db,
            "UPDATE Users SET Campaigns=%s WHERE Id=%s;",
            (json.dumps(campaigns), id_),
        )
        == False
    ):
        return False
    return True


def get_dm_id(db: mysql.MySQLConnection, code: str) -> Literal[False] | int:
    """Ottieni l'id del dungeon master di una campagna.

    Args:
        db (mysql.MySQLConnection): Una connessione a un database.
        code (str): Il codice di una campagna

    Returns:
        Literal[False] | int: L'id del dungeon master, False in caso di errore.
    """

    dm_id = functions.SQL_query(
        db, "SELECT * FROM Campaigns WHERE Code=%s;", (code,), single=True
    )
    if dm_id == False:
        return False
    return dm_id["DungeonMaster"]


def delete_campaign(db: mysql.MySQLConnection, code: str) -> bool:
    """Cancella una campagna.

    Args:
        db (mysql.MySQLConnection): Una connessione a un database.
        code (str): Il codice della campagna da cancellare.

    Returns:
        bool: True se tutto è andato a buon fine, altrimenti False.
    """

    CampaignDb = functions.db_connect(
        config.DB_HOST_NAME,
        config.DB_HOST_PORT,
        config.DB_USER_NAME,
        config.DB_USER_PASSWORD,
        f"dnd_site_campaign_{code}",
    )
    if CampaignDb == False:
        return False

    if (
        functions.SQL_query(
            CampaignDb, "DROP DATABASE `%s`;" % f"dnd_site_campaign_{code}")
        == False
    ):
        return False

    if (
        functions.SQL_query(
            db,
            "DELETE FROM Campaigns WHERE Code=%s;",
            (code,),
        )
        == False
    ):
        return False
    return True


def join_campaign(db: mysql.MySQLConnection, code: str, id_: int, name: str) -> bool:
    """Unisce un giocatore a una campagna.

    Args:
        db (mysql.MySQLConnection): Una connessione al database.
        code (str): Il codice della campagna.
        id_ (int): L'id del giocatore.
        name (str): Il nome con cui il giocatore vuole essere conosciuto.

    Returns:
        bool: True se è andato tutto bene altrimenti False.
    """
    CampaignDb = functions.db_connect(
        config.DB_HOST_NAME,
        config.DB_HOST_PORT,
        config.DB_USER_NAME,
        config.DB_USER_PASSWORD,
        f"dnd_site_campaign_{code}",
    )
    if CampaignDb == False:
        return False

    if (
        functions.SQL_query(
            CampaignDb,
            "INSERT INTO Players (UserId, Name) VALUES (%s, %s);",
            (id_, name),
        )
        == False
    ):
        return False

    campaigns = functions.get_user_campaigns(db, id_)
    if campaigns == False:
        return False

    campaign_players = get_campaign_players(db, code)
    if campaign_players == False:
        return False

    campaign = functions.get_campaign_from_code(db, code)
    if campaign == False:
        return False

    campaign_players.append(id_)

    if (
        functions.SQL_query(
            db,
            "UPDATE Campaigns SET Players=%s WHERE Code=%s;",
            (json.dumps(campaign_players), code),
        )
        == False
    ):
        return False

    campaigns.append(
        {
            "href": url_for("campaign", code=code),
            "code": code,
            "name": campaign["CampaignName"],
        }
    )
    if (
        functions.SQL_query(
            db,
            "UPDATE Users SET Campaigns=%s WHERE Id=%s;",
            (json.dumps(campaigns), id_,),
        )
        == False
    ):
        return False

    return True
