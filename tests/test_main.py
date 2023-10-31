import unittest
import os
from dotenv import load_dotenv
from src.main import connection
from utils.constants import ENV_FILE_PATH
import logging

load_dotenv(dotenv_path=ENV_FILE_PATH, verbose=True)


class TestMain(unittest.TestCase):

    def test_connection(self):
        server = os.getenv("IMAP_SERVER")
        user = os.getenv("RECEIVER_EMAIL")
        password = os.getenv("RECEIVER_PASSWORD")
        con = connection(server=server, user=user, password=password)

        self.assertIsNone(con)


if __name__ == '__main__':
    unittest.main()
