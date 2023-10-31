import unittest
from src.credit import *


class CreditTest(unittest.TestCase):

    def test_is_credit_by_alert(self):
        transaction_information = {
            "Jake just sent you #1200"
        }
        res = is_credit_by_alert(transaction_information)
        self.assertIsInstance(res, bool)

    def test_is_credit_by_withdrawal(self):
        transaction_header = 'We Reversed Some Money Into Your Account'
        res = is_credit_by_reversal(transaction_header)
        self.assertIsInstance(res, bool)

    def test_get_credit_sender(self):
        transaction_info = "Jack just sent you ₦25,000.00. "
        res = get_credit_by_alert_info(transaction_info)
        self.assertEqual(res.get("sender"), "Jack")


if __name__ == "__main__":
    unittest.main()
