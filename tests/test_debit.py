import unittest

from src.debit import *

TRANSFER_DEBIT = "You just sent ₦800.00 to  Jack - Gum. "
AIRTIME_DEBIT = "You just recharged MTN NG VTU 2348102462547 - Airtime with ₦6,000.00"
CARD_ONLINE_TRANSACTION_HEADER = 'You Used Your Kuda Card Online'
CARD_POS_TRANSACTION_HEADER = 'You Used Your Kuda Card On A POS'
CARD_SPEND_AND_SAVE_TRANSACTION_HEADER = 'You Saved Some Money'


class TestDebit(unittest.TestCase):

    def test_is_debit_by_airtime_recharge(self):
        res = is_debit_by_airtime_recharge(AIRTIME_DEBIT)
        self.assertEqual(res, True)

    def test_is_debit_by_transfer(self):
        res = is_debit_by_transfer(TRANSFER_DEBIT)
        self.assertEqual(res, True)

    def test_is_debit_by_card_online(self):
        res = is_debit_by_card_online(CARD_ONLINE_TRANSACTION_HEADER)
        self.assertEqual(res, True)

    def test_is_debit_by_card_pos(self):
        res = is_debit_by_card_pos(CARD_POS_TRANSACTION_HEADER)
        self.assertEqual(res, True)

    def test_is_debit_by_spend_and_save(self):
        res = is_debit_by_spend_and_save(CARD_SPEND_AND_SAVE_TRANSACTION_HEADER)
        self.assertEqual(res, True)

    def test_process_receiver(self):
        res = process_receiver(TRANSFER_DEBIT)
        self.assertEqual(res, "Jack")

    def test_debit_description(self):
        res = get_debit_by_alert_info(TRANSFER_DEBIT)
        self.assertEqual(res.get("description"), "Gum")

    def test_get_airtime_info(self):
        res = get_debit_by_airtime_info(AIRTIME_DEBIT)
        self.assertEqual(res.get("network"), "MTN")

    def test_get_phone_number(self):
        res = get_debit_by_airtime_info(AIRTIME_DEBIT)
        self.assertEqual(res.get("phone_number"), "08102462547")


if __name__ == "__main__":
    unittest.main()
