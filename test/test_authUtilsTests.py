import asyncio
import os
import unittest
from datetime import timedelta

from fastapi import HTTPException

from authUtils import hash_password, authenticate_user, create_access_token, get_user_from_token
import database

os.environ["SECRET_KEY"] = "8e0d8bd41ce4418a57bf350557c59b27496c6b48d42e5cff859830c23a3233a4"
os.environ["ALGORITHM"] = "HS256"


class AuthUtilsTests(unittest.IsolatedAsyncioTestCase):
    def test_authenticate_user(self):
        user = database.get_user("username")

        self.assertEqual(user, authenticate_user("username", "password"))
        self.assertEqual(None, authenticate_user("username", "wrong_password"))
        self.assertEqual(None, authenticate_user("wrong_username", "password"))

    async def test_token(self):
        user = database.get_user("username")

        token = create_access_token("username")
        self.assertEqual(user, await get_user_from_token(token))

        token_with_invalid_user = create_access_token("invalid_username")
        with self.assertRaises(HTTPException):
            await get_user_from_token(token_with_invalid_user)

        expired_token = create_access_token("username", timedelta(seconds=-1))
        with self.assertRaises(HTTPException):
            await get_user_from_token(expired_token)

        expired_token_with_invalid_user = create_access_token("invalid_username", timedelta(seconds=-1))
        with self.assertRaises(HTTPException):
            await get_user_from_token(expired_token_with_invalid_user)

    def tearDown(self) -> None:
        super().tearDown()
        database._reset()

    def setUp(self) -> None:
        super().setUp()
        database._database_init()
        database.create_user("username", hash_password("password"))


if __name__ == '__main__':
    unittest.main()
