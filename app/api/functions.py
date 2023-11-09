from flask import session
from pathlib import Path
from os import remove
from typing import Literal
import re as regex
import sqlite3
import hashlib


class SqliteDatabase:
    def __init__(self, path: str) -> None:
        self.__path = Path(path).resolve()
        dir = self.__path.parent
        if not dir.exists(): 
            dir.mkdir(parents=True, exist_ok=True)
            with open(self.__path, "x") as f: ...

        self.__conn = sqlite3.connect(path)

    @property
    def path(self) -> Path:
        return self.__path

    @property
    def conn(self) -> sqlite3.Connection:
        return self.__conn

    def execute(self, sqlQuery: str, sqlParam: tuple | dict = None) -> list:
        if sqlParam is None:
            sqlParam = ()

        # Inizializza il cursore
        cur = self.conn.cursor()

        # Esegui la query aggiornando il database se necessario
        cur.execute(sqlQuery, sqlParam)
        if (sqlQuery.find("UPDATE")
            or sqlQuery.find("DELETE")
            or sqlQuery.find("INSERT")):
            self.conn.commit()

        # Get all the resoults of the query
        res = cur.fetchall()

        # Chiudi il cursore
        cur.close()
        return res

    def delete(self):
        self.__conn.close()
        remove(self.path)


def start_database(dbPath: str) -> SqliteDatabase:
    UsersDb = SqliteDatabase("db/Users.sqlite3")
    UsersDb.execute(
        """CREATE TABLE IF NOT EXISTS Players (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            PlayerName TEXT NOT NULL,
            Pwd TEXT NOT NULL,
            Campaign TEXT)
            """
    )
    return UsersDb


def empty_input(*args: str) -> bool:
    for i in args:
        if not i:
            return True
    return False


def invalid_name(name: str) -> bool:
    if not regex.match(r"^[a-zA-Z_]{4,32}$", name):
        return True
    return False


def get_name(conn: SqliteDatabase, name: str) -> Literal[False] | list:
    row = conn.execute("SELECT * FROM Players WHERE PlayerName = ?", (name,))
    if row:
        return row
    return False


def create_player(conn: SqliteDatabase, name: str, pwd: str) -> None:
    hashedPwd = hash_password(pwd)
    conn.execute(
        "INSERT INTO Players (PlayerName, Pwd) VALUES (?, ?)", (name, hashedPwd)
    )


def login_player(conn: SqliteDatabase, name: str, pwd: str) -> bool:
    getNameResult = get_name(conn, name)

    if not getNameResult:
        return False

    pwdHashed = getNameResult[2]

    if not verify_password(pwd, pwdHashed):
        return False
    session["Id"] = getNameResult[0]
    session["PlayerName"] = getNameResult[1]
    return True


def search_player(conn: SqliteDatabase, name: str) -> dict[str, str | list | None]:
    result = conn.execute(
        "SELECT * FROM Players WHERE PlayerName LIKE ?", (f"%{name}%",)
    )

    if len(result) > 0:
        return {"name": name, "result": result[0]}
    else:
        return {"name": name, "result": None}


def get_players(conn: SqliteDatabase, campaign: str) -> dict[str, list] | None:
    result = conn.execute("SELECT * FROM Players WHERE Campaign=?", (campaign,))
    if result:
        return {"result": result}
    else:
        return None


def hash_password(password: str) -> str:
    hashedPassword = hashlib.sha256(password.encode()).hexdigest()
    return hashedPassword


def verify_password(inputPwd: str, hashedPwd: str) -> bool:
    return hashlib.sha256(inputPwd.encode()).hexdigest() == hashedPwd
