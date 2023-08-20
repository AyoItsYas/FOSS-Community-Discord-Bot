from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union, Iterable

    from mysql.connector import MySQLConnection
    from mysql.connector.pooling import PooledMySQLConnection

    from core.database.models.User import User


import mysql.connector


class Client:
    def __init__(self):
        self.database: Union[MySQLConnection, PooledMySQLConnection] = None

    def connect(self, *args, **kwargs) -> Union[MySQLConnection, PooledMySQLConnection]:
        self.database = mysql.connector.connect(*args, **kwargs)

        return self.database

    def close(self):
        self.database.close()

    def disconnect(self):
        self.database.disconnect()

    def get_user(self) -> User:
        pass

    def get_users(self) -> Iterable[User]:
        pass

    def modify_user(self):
        pass

    def modify_users(self):
        pass
