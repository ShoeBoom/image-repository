# TODO: implement salting
import sqlite3
from typing import Optional, List

from pydantic import BaseModel

connection = sqlite3.connect("database.db")


def _database_init():
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS user_table(username TEXT PRIMARY KEY, password_hash TEXT NOT NULL );")
    cursor.execute("CREATE TABLE IF NOT EXISTS images(image_id TEXT PRIMARY KEY, username TEXT, "
                   "private_int INTEGER NOT NULL, FOREIGN KEY (username) REFERENCES user_table(username));")
    connection.commit()
    cursor.close()


def _reset():
    cursor = connection.cursor()
    cursor.execute("DROP TABLE user_table;")
    cursor.execute("DROP TABLE images;")
    connection.commit()
    cursor.close()


def create_image(image_id: str, username: Optional[str], private: bool) -> bool:
    cursor = connection.cursor()
    # need to convert bool to int due to sqllite not having bool
    private_int = 1 if private else 0
    try:
        cursor.execute("INSERT INTO images VALUES (?, ?, ?);", (image_id, username, private_int))
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        cursor.close()


class ImageInDB(BaseModel):
    image_id: str
    username: Optional[str]
    private: bool


def get_image(image_id: str) -> Optional[ImageInDB]:
    cursor = connection.cursor()
    result = cursor.execute("SELECT * FROM images WHERE image_id=?;", (image_id,)).fetchall()
    cursor.close()
    if len(result) == 0:
        return None
    else:
        private_bool = result[0][2] == 1
        return ImageInDB(image_id=result[0][0], username=result[0][1], private=private_bool)


def get_images_from_username(username: str) -> List[ImageInDB]:
    cursor = connection.cursor()
    result = cursor.execute("SELECT * FROM images WHERE username=?;", (username,)).fetchall()
    cursor.close()

    result_list = [
        ImageInDB(image_id=im_id, username=username, private=(True if private_int == 1 else False))
        for im_id, username, private_int in result
    ]
    return result_list


def delete_image(image_id: str):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM images WHERE image_id=?;",
                   (image_id, ))
    connection.commit()

    cursor.close()


def create_user(username: str, password_hash: str) -> bool:
    """
    creates a user in the database
    :param username: the username
    :param password_hash: the hashed password
    :return: true is successful false if user already exists
    """
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO user_table VALUES (?, ?);", (username, password_hash))
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        cursor.close()


class UserInDB(BaseModel):
    username: str
    password_hash: str


def get_user(username: str) -> Optional[UserInDB]:
    """
    get password hash from username
    :return: the password hash
    """
    cursor = connection.cursor()
    result = cursor.execute("SELECT * FROM user_table WHERE username=?;", (username,)).fetchall()
    cursor.close()
    if len(result) == 0:
        return None
    else:
        return UserInDB(username=result[0][0], password_hash=result[0][1])


_database_init()
