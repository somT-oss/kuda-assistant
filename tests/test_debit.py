import unittest
from src.debit import (
    is_debit_by_airtime_recharge,
    is_debit_by_transfer,
    is_debit_by_card_online,
    get_service_for_online_card_payment,
    is_debit_by_card_pos,
    is_debit_by_spend_and_save,
    get_savings_pocket,
    get_narration_and_receiver
)

class TestDebit(unittest.TestCase):
    def test_debit_by_airtime_recharge(self):
        data = "You just recharged ₦1,000.00 airtime for 08031234567".lower()
        self.assertEqual(is_debit_by_airtime_recharge(data), True)

    def test_false_debit_by_airtime_recharge(self):
        data = "John Doe just sent you ₦1,000,000.00.".lower()
        self.assertEqual(is_debit_by_airtime_recharge(data), False)

    def test_debit_by_transfer(self):
        data = "You just sent ₦1,000.00 to John Doe - Rent".lower()
        self.assertEqual(is_debit_by_transfer(data), True)

    def test_false_debit_by_transfer(self):
        data = "You sent ₦1,000,000.00 to John Doe".lower()
        self.assertEqual(is_debit_by_transfer(data), False)
    
    def test_is_debit_by_card_online(self):
        data = "You paid ₦1,000 with your kuda card on amazon".lower()
        self.assertEqual(is_debit_by_card_online(data), True)

    def test_false_is_debit_by_card_online(self):
        data = "John Doe just sent you ₦1,000,000".lower()
        self.assertEqual(is_debit_by_card_online(data), False)
    
    def test_get_service_for_online_card_payment(self):
        data = "You paid ₦1,000 with your kuda card on amazon.".lower()
        self.assertEqual(get_service_for_online_card_payment(data), "amazon")

    def test_is_debit_by_card_pos(self):
        data = "You used your card on a pos".lower()
        self.assertEqual(is_debit_by_card_pos(data), True)

    def test_false_is_debit_by_card_pos(self):
        data = "John Doe just sent you ₦1,000,000".lower()
        self.assertEqual(is_debit_by_card_pos(data), False)
    
    def test_is_debit_by_spend_and_save(self):
        data = "We moved ₦1,000 from your spend account to your personal savings".lower()
        self.assertEqual(is_debit_by_spend_and_save(data), True)

    def test_false_is_debit_by_spend_and_save(self):
        data = "John Doe just sent you ₦1,000,000".lower()
        self.assertEqual(is_debit_by_spend_and_save(data), False)
    
    def test_get_savings_pocket(self):
        data = "We moved ₦1,000 from your spend account to reserve savings".lower()
        self.assertEqual(get_savings_pocket(data), "reserve")

    def test_false_get_savings_pocket(self):
        data = "John Doe just sent you ₦1,000,000".lower()
        self.assertEqual(get_savings_pocket(data), None)
    
    def test_get_narration_and_receiver(self):
        data = "You just sent ₦1,000 to John Doe - Rent. love".lower()
        self.assertEqual(get_narration_and_receiver(data), {"receiver": "john doe", "description": "rent"})

    def test_false_get_narration_and_receiver(self):
        data = "John Doe just sent you ₦1,000,000".lower()
        self.assertEqual(get_narration_and_receiver(data), None)
    
if __name__ == "__main__":
    unittest.main()
