import unittest

from src.credit import (
    is_credit_by_reversal,
    is_credit_by_transfer,
    is_credit_by_removal_from_savings,
    get_savings_pocket
)


class TestCredit(unittest.TestCase):
    def test_credit_by_reversal(self):
        data = "You tried to make a transfer of ₦1,000,000.00., and it didn't go through so we've reversed it.".lower()
        self.assertEqual(is_credit_by_reversal(data), True)

    def test_false_credit_by_reversal(self):
        data = "John Doe may have sent you ₦1,000,000".lower()
        self.assertEqual(is_credit_by_reversal(data), False)

    def test_is_credit_by_transfer(self):
        data = "John Doe just sent you ₦1,000,000".lower()
        self.assertEqual(is_credit_by_transfer(data), True)

    def test_false_is_credit_by_transfer(self):
        data = "John Doe may have sent you ₦1,000,000".lower()
        self.assertEqual(is_credit_by_transfer(data), False)

    def test_credit_by_removal_from_savings(self):
        data = "You took out ₦1,000,000.00 from your personal savings.".lower()
        self.assertEqual(is_credit_by_removal_from_savings(data), True)

    def test_false_credit_by_removal_from_savings(self):
        data = "John Doe just sent you ₦1,000,000".lower()
        self.assertEqual(is_credit_by_removal_from_savings(data), False)

    def test_savings_pocket(self):
        data = "You took out ₦1,000,000.00 from your personal savings.".lower()
        self.assertEqual(get_savings_pocket(data), "personal")

    def test_false_savings_pocket(self):
        data = "John Doe just sent you ₦1,000,000".lower()
        self.assertEqual(get_savings_pocket(data), None)
