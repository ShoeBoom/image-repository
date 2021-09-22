import unittest
import database
from database import *


class DatabaseTests(unittest.TestCase):
    def test_user(self):
        # returns none when user does not exist
        self.assertEqual(None, database.get_user("test"))

        # is able to successfully create user in database
        self.assertEqual(True, create_user("test", "test pass"))
        self.assertEqual(UserInDB(username="test", password_hash="test pass"), database.get_user("test"))

        # fails to create duplicate
        self.assertEqual(False, create_user("test", "test pass"))

    def test_image(self):
        # returns none when image does not exist
        self.assertEqual(None, database.get_image("test"))

        # is able to successfully create image in database
        self.assertEqual(True, create_image("testid", None, False))
        self.assertEqual(True, create_image("testid2", "user", False))
        self.assertEqual(True, create_image("testid3", "user", True))

        # get_image provides correct values
        self.assertEqual(ImageInDB(image_id="testid", username=None, private=False), database.get_image("testid"))
        self.assertEqual(ImageInDB(image_id="testid2", username="user", private=False), database.get_image("testid2"))
        self.assertEqual(ImageInDB(image_id="testid3", username="user", private=True), database.get_image("testid3"))

        # test get image by suer functionality
        self.assertEqual([ImageInDB(image_id='testid2', username='user', private=False),
                          ImageInDB(image_id='testid3', username='user', private=True)],
                         database.get_images_from_username("user"))
        print()

        # images are deleted properly
        database.delete_image("testid")
        database.delete_image("testid2")
        database.delete_image("testid3")
        self.assertEqual(None, database.get_image("testid"))
        self.assertEqual(None, database.get_image("testid2"))
        self.assertEqual(None, database.get_image("testid3"))

        # fails to create duplicate
        create_image("testid", None, False)
        self.assertEqual(False, create_image("testid", None, False))
        self.assertEqual(False, create_image("testid", "user", False))
        self.assertEqual(False, create_image("testid", "user", True))

    def tearDown(self) -> None:
        super().tearDown()
        database._reset()

    def setUp(self) -> None:
        super().setUp()
        database._database_init()
        create_user("user", "pass")


if __name__ == '__main__':
    unittest.main()
