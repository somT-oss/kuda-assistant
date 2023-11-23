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

    def test_mongo_connection(self):
        mongo_con = mongo_connection()

        self.assertIsNotNone(mongo_con)

    def test_process_read_transactions(self):
        db = mongo_connection().get_database(DATABASE)
        read_transaction_receipts = db.get_collection(READ_TRANSACTION_RECEIPTS).find({"date": "2023-11-20"})

        for transactions in read_transaction_receipts:
            res = ReadTransactionProcessor.process_read_transactions(transactions)

            self.assertIsInstance(res, dict)

    def test_process_unread_transactions(self):
        db = mongo_connection().get_database(DATABASE)
        unread_transaction_receipts = db.get_collection(UNREAD_TRANSACTION_RECEIPTS).find({"date": "2023-11-20"})

        for transactions in unread_transaction_receipts:
            res = UnreadTransactionsProcessor.process_unread_transactions(transactions)

            self.assertIsInstance(res, dict)

    # UNCOMMENT TO TEST SCRAPER FUNCTION

    # def test_scraper(self):
    #     con = connection(SERVER, USER, PASSWORD)
    #     mongo_con = mongo_connection()
    #
    #     scrape = scraper(con, mongo_con, KUDA)
    #     self.assertIsNone(scrape)

    def test_compute_transaction(self):

        mongo_con = mongo_connection()
        compute = compute_transaction(mongo_con)

        self.assertIsNotNone(compute, list)

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
