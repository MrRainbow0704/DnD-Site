import mysql.connector as mysql
from typing import Literal


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
    # Inizializza il cursore
    cur = conn.cursor(dictionary=True)
    # Esegui la query aggiornando il database
    try:
        cur.execute(sqlString, sqlParam)
        if (
            sqlString.count("INSERT")
            or sqlString.count("UPDATE")
            or sqlString.count("DELETE")
        ):
            conn.commit()
    except mysql.Error as err:
        print(f"Error: '{err} {sqlString=} {sqlParam=}'")
        conn.rollback()
        return False

    # Ottieni i risultati della query.
    try:
        res = cur.fetchall()
    except mysql.Error as err:
        print(f"Error: '{err}'")
        res = [None]

    # if single:
    #     res = res[0]

    # Chiudi il cursore
    print(res)
    cur.reset()
    cur.close()
    return res


def create_db(
    DbHostName: str,
    DbUserPort: int,
    DbUserName: str,
    DbUserPassword: str,
    DbName: str,
) -> mysql.MySQLConnection:
    """Crea un database e restituisce la connessione a esso.
    ATTENZIONE DbName è vulnerabile a iniezioni SQL! Sanificalo.

    Args:
        DbHostName (str): IP del database.
        DbHostPort (int): Porta del database.
        DbUserName (str): Username con il quale loggare.
        DbUserPassword (str): Password con la quale loggare.
        DbName (str): Nome del database da creare.

    Returns:
        mysql.MySQLConnection: Connessione al database selezionato.
    """
    try:
        conn = mysql.connect(
            host=DbHostName, port=DbUserPort, user=DbUserName, passwd=DbUserPassword
        )
    except mysql.Error as err:
        conn = False
        print(f"Error: '{err}'")
    SQL_query(conn, "CREATE DATABASE IF NOT EXISTS `%s`;" % DbName)
    return db_connect(DbHostName, DbUserPort, DbUserName, DbUserPassword, DbName)
