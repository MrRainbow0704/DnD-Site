from flask import session
from typing import Literal, Any
import mysql.connector as mysql
import re as regex
import hashlib
from config import PEPPER
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
        name (str): Nome da conrollare.

    Returns:
        bool: Se il nome è valido o no.
    """

    # Controlla se il nome contione solo lettere, numeri o _
    # e se ha una lunghezza tra i 4 e i 32 caratteri
    if not regex.match(r"^[a-zA-Z0-9_]{4,32}$", name):
        return True
    return False


def get_name(db: mysql.MySQLConnection, name: str) -> Literal[False] | dict:
    """Ottiene tutte le righe di un utente in base al suo nome.

    Args:
        db (mysql.MySQLConnection): Connessione a un database.
        name (str): Nome dell'utente.

    Returns:
        Literal[False] | dict: Un dizionario rappresentante la riga. Se non trova nulla False.
    """

    # Chiede al database tutte le righe della tabella `Users` che hanno il nome indicato
    row = functions.SQL_query(
        db, "SELECT * FROM Users WHERE UserName = %s;", (name,), single=True
    )
    if row:
        return row
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
    getNameResult = get_name(db, name)

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
    return hashlib.sha512(str(salt + password + PEPPER).encode()).hexdigest()


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
