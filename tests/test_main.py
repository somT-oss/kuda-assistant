import unittest

from src.main import *
from utils.constants import ENV_FILE_PATH

load_dotenv(dotenv_path=ENV_FILE_PATH, verbose=True)

SERVER = os.getenv("IMAP_SERVER")
USER = os.getenv("RECEIVER_EMAIL")
PASSWORD = os.getenv("RECEIVER_PASSWORD")
KUDA = os.getenv("KUDA")


class TestMain(unittest.TestCase):

    def test_connection(self):
        con = connection(server=SERVER, user=USER, password=PASSWORD)

        self.assertIsNotNone(con)

    def test_process_unseen_messages(self):

        con = connection(SERVER, USER, PASSWORD)
        res = process_unseen_messages(con, KUDA)

        self.assertIsInstance(res, dict)

    def test_process_seen_messages(self):

        con = connection(SERVER, USER, PASSWORD)
        res = process_seen_messages(con, KUDA)

        self.assertIsInstance(res, dict)

    def test_get_seen_messages(self):

        res = get_seen_messages_details()
        self.assertIsInstance(res, list)

    def test_get_unseen_messages(self):

        res = get_unseen_messages_details()
        self.assertIsInstance(res, list)

    def test_process_debit(self):

        seen_transaction_holder = get_seen_messages_details()
        unseen_transaction_holder = get_unseen_messages_details()

        if seen_transaction_holder[0].get("error") is None:
            res = process_debit(unseen_transaction_holder)
            self.assertIsInstance(res, dict)

        if unseen_transaction_holder[0].get("error") is None:
            res = process_debit(seen_transaction_holder)
            self.assertIsInstance(res, dict)

        if seen_transaction_holder[0].get("error") and unseen_transaction_holder[0].get("error") is None:
            merged_transaction_holder = seen_transaction_holder + unseen_transaction_holder
            res = process_debit(merged_transaction_holder)
            self.assertIsInstance(res, dict)

    def test_process_credit(self):

        seen_transaction_holder = get_seen_messages_details()
        unseen_transaction_holder = get_unseen_messages_details()

        if seen_transaction_holder[0].get("error") is None:
            res = process_credit(unseen_transaction_holder)
            self.assertIsInstance(res, dict)

        if unseen_transaction_holder[0].get("error") is None:
            res = process_credit(seen_transaction_holder)
            self.assertIsInstance(res, dict)

        if seen_transaction_holder[0].get("error") and unseen_transaction_holder[0].get("error") is None:
            merged_transaction_holder = seen_transaction_holder + unseen_transaction_holder
            res = process_credit(merged_transaction_holder)
            self.assertIsInstance(res, dict)

    def test_write_debit_to_excel(self):

        test_debit_alert = {
            "debit_alert": [{
                "AIRTIME RECHARGE": "True",
                "AMOUNT": 100,
                "DATE": "2023-10-12"
            }],
            "no_of_debit_alert": 1
        }

        res = write_debit_to_excel(test_debit_alert)
        self.assertEqual(res, "Done")

    def test_write_credit_to_excel(self):
        test_credit_alert = {
            "credit_alert": [{
                "CREDIT BY ALERT": "True",
                "AMOUNT": 100,
                "DATE": "2023-10-12"
            }],
            "no_of_debit_alert": 1
        }

        res = write_credit_to_excel(test_credit_alert)
        self.assertEqual(res, "Done")


if __name__ == '__main__':
    unittest.main()
