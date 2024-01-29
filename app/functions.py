"""Un modulo con delle funzioni utili usate da tutta l'applicazione"""

from flask import session
import mysql.connector as mysql
from typing import Literal
import json


def db_connect(
    DbHostName: str, DbHostPort: int, DbUserName: str, DbUserPassword: str, DbName: str
) -> mysql.MySQLConnection | None:
    """Crea e restituisce una connessione a un database già esistente.

    Args:
        DbHostName (str): IP del database.
        DbHostPort (int): Porta del database.
        DbUserName (str): Username con il quale loggare.
        DbUserPassword (str): Password con la quale loggare.
        DbName (str): Nome del database a cui connettersi.

    Returns:
        mysql.MySQLConnection: Connessione al database selezionato.
    """

    # Prova a stabilire una connessione con il database, se fallisce restituisce False
    connection = False
    try:
        connection = mysql.connect(
            host=DbHostName,
            port=DbHostPort,
            user=DbUserName,
            passwd=DbUserPassword,
            database=DbName,
        )
    except mysql.Error as err:
        print(f"Error: '{err}'")

    return connection


def SQL_query(
    conn: mysql.MySQLConnection,
    sqlString: str,
    sqlParam: tuple | dict = None,
    single=False,
) -> dict[str, str] | list[dict[str, str] | None] | None | Literal[False]:
    """Fa una richiesta al database e restituisce la risposta. Tutti i parametri vengono sanificati automaticamente.

    Args:
        conn (mysql.MySQLConnection): Una connessione al database.
        sqlString (str): IL comando da eseguire. Usa %s come placeholder o
                        %(var)s se sqlParam è un dizionario con una chiave "val".
        sqlParam (tuple | dict, optional): Parametri da associare al comando. Defaults to None.
        single (bool, optional): Se ci si aspetta una singola riga. Defaults to False.

    Returns:
        dict[str, str] | list[dict[str, str] | None] | None | False : Le/la righe/a restituite/a dalla
                                richiesta, False se la richiesta fallisce.
    """

    if sqlParam is None:
        sqlParam = ()

    cur = conn.cursor(dictionary=True)

    # Esegui la query aggiornando il database se necessario
    # Se la query fallisce, fa il rollback e restituisce False
    try:
        cur.execute(sqlString, sqlParam)
        if (
            sqlString.count("INSERT")
            or sqlString.count("UPDATE")
            or sqlString.count("DELETE")
        ):
            conn.commit()
    except mysql.Error as err:
        print(f"Error: '{err}'")
        conn.rollback()
        return False

    # Ottieni i risultati della query svuotando anche il buffer
    try:
        res = cur.fetchall()
    except mysql.Error as err:
        print(f"Error: '{err}'")
        res = [None]

    # Gestisci le query singole per non avere liste con un unico indice
    if single:
        try:
            res = res[0]
        except IndexError:
            res = []

    # Chiudi il cursore e restituisci il risultato della query
    cur.reset()
    cur.close()
    return res


def create_db(
    DbHostName: str,
    DbUserPort: int,
    DbUserName: str,
    DbUserPassword: str,
    DbName: str,
) -> mysql.MySQLConnection | Literal[False]:
    """Crea un database e restituisce la connessione a esso.
    ATTENZIONE DbName è vulnerabile a iniezioni SQL! Sanificalo.

    Args:
        DbHostName (str): IP del database.
        DbHostPort (int): Porta del database.
        DbUserName (str): Username con il quale loggare.
        DbUserPassword (str): Password con la quale loggare.
        DbName (str): Nome del database da creare.

    Returns:
        mysql.MySQLConnection | Literal[False]: Connessione al database selezionato, false se fallisce.
    """

    # Prova a creare una connessione a un database senza specificare la tabella.
    # Se va a buon fine, crea la tabella richiesta e restituisci una connessione al database
    # altrimenti restituisci false
    try:
        conn = mysql.connect(
            host=DbHostName, port=DbUserPort, user=DbUserName, passwd=DbUserPassword
        )
    except mysql.Error as err:
        print(f"Error: '{err}'")
        return False
    else:
        SQL_query(conn, "CREATE DATABASE IF NOT EXISTS `%s`;" % DbName)
        return db_connect(DbHostName, DbUserPort, DbUserName, DbUserPassword, DbName)


def get_user_from_name(db: mysql.MySQLConnection, name: str) -> Literal[False] | dict:
    """Ottiene tutte le righe di un utente in base al suo nome.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        name (str): Nome dell'utente.

    Returns:
        Literal[False] | dict: Un dizionario rappresentante la riga. Se non trova nulla False.
    """

    # Chiede al database tutte le righe della tabella `Users` che hanno il nome indicato
    row = SQL_query(
        db, "SELECT * FROM Users WHERE UserName = %s;", (name,), single=True
    )
    if row:
        return row
    return False


def get_user_from_id(db: mysql.MySQLConnection, id_: int) -> Literal[False] | dict:
    """Ottiene tutte le righe di un utente in base al suo nome.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        id_ (int): Id dell'utente.

    Returns:
        Literal[False] | dict: Un dizionario rappresentante la riga. Se non trova nulla False.
    """

    # Chiede al database tutte le righe della tabella `Users` che hanno l'id indicato
    row = SQL_query(db, "SELECT * FROM Users WHERE Id = %s;", (id_,), single=True)
    if row:
        return row
    return False


def get_player_from_id(db: mysql.MySQLConnection, id_: str) -> Literal[False] | dict:
    """Ottiene tutte le righe di un giocatore in base al suo nome.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        id_ (str): Id dell'utente.

    Returns:
        Literal[False] | dict: Un dizionario rappresentante la riga. Se non trova nulla False.
    """

    # Chiede al database tutte le righe della tabella `Users` che hanno l'id indicato
    row = SQL_query(db, "SELECT * FROM Players WHERE Id=%s;", (id_,), single=True)
    if row != False:
        return row
    return False


def get_campaign_from_code(
    db: mysql.MySQLConnection, code: str
) -> Literal[False] | dict:
    """Ottiene tutte le righe di una campagna in base al suo id.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        code (str): Id della campagna.

    Returns:
        Literal[False] | dict: Un dizionario rappresentante la riga. Se non trova nulla False.
    """

    # Chiede al database tutte le righe della tabella `Users` che hanno l'id indicato
    row = SQL_query(db, "SELECT * FROM Campaigns WHERE Code=%s;", (code,), single=True)
    if row:
        return row
    return False


def is_logged_in() -> bool:
    """Controlla se l'utente è loggato o no.

    Returns:
        bool: True se l'utente è loggato, altrimenti False.
    """

    return "Id" in session


def get_user_campaigns(
    db: mysql.MySQLConnection, id_: int
) -> list[dict] | Literal[False]:
    """Ottieni tutte le campagne a cui partecipa un utente.

    Args:
        db (mysql.MySQLConnection): Una connessione al database.
        id (str): Id dell'utente.

    Returns:
        list[dict] | Literal[False]: Una lista di tutte le campagne a cui l'utente partecipa.
    """

    res = get_user_from_id(db, id_)
    if res == False:
        return False
    return json.loads(res["Campaigns"])
