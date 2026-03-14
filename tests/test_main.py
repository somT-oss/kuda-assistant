import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock


from src.main import (
    login,
    redis_conn,
    parse_debit_transaction,
    parse_credit_transaction,
)


class TestIMAPConnection(unittest.TestCase):
    @patch("src.main.MailBox")
    def test_login_success(self, mailbox):
        fake_mailbox = MagicMock()
        mailbox.return_value = fake_mailbox

        fake_mailbox.login.return_value = fake_mailbox

        res = login("imap.gmail.com", "john", "testing321")
        
        mailbox.assert_called_once_with("imap.gmail.com")
        fake_mailbox.login.assert_called_once_with("john", "testing321")

        self.assertEqual(res, fake_mailbox)
    

class TestRedisConnection(unittest.TestCase):
    
    @patch("src.main.redis.from_url")
    @patch("src.main.os.getenv")
    def test_redis_conn(self, mock_getenv, mock_from_url):
        redis_url = "redis://localhost:6379/0"
        mock_getenv.return_value = redis_url
        fake_client = MagicMock()
        mock_from_url.return_value = fake_client
        
        res = redis_conn()
        
        mock_getenv.assert_called_once_with("REDIS_URL")
        mock_from_url.assert_called_once_with(redis_url)
        
        self.assertEqual(res, fake_client)


class TestParseTransaction(unittest.TestCase):
    
    def test_parse_debit_transaction(self):
        transfer_data = {
            "trxn_statement": "You just sent ₦1,000 to John Doe - Rent. love".lower(),
            "date": "2026-01-02"
        }
        
        airtime_data = {
            "trxn_statement": "You just recharged MTN NG VTU 08031234567 - Airtime with ₦500.00".lower(),
            "date": "2026-01-02"
        }
        
        used_your_card_online_data = {
            "trxn_statement": "You paid ₦1,000 with your kuda card on amazon. love".lower(),
            "date": "2026-01-02"
        }
        
        used_card_in_pos_data = {
            "trxn_statement": "You used your card on a pos to withdraw ₦1,000. love".lower(),
            "date": "2026-01-02"
        }
        
        
        # test transfer debit transaction
        transfer_debit_trxn = parse_debit_transaction(transfer_data)
        self.assertEqual(transfer_debit_trxn['amount'], 1000)
        self.assertEqual(transfer_debit_trxn['date_of_transaction'], datetime.strptime(transfer_data['date'], "%Y-%m-%d"))
        self.assertEqual(transfer_debit_trxn['debit_metadata'], {'narration': 'rent', 'receiver': 'john doe', 'transfer': True})
    
        # test airtime debit transaction
        airtime_debit_trxn = parse_debit_transaction(airtime_data)
        self.assertEqual(airtime_debit_trxn['amount'], 500)
        self.assertEqual(airtime_debit_trxn['date_of_transaction'], datetime.strptime(transfer_data['date'], "%Y-%m-%d"))
        self.assertEqual(airtime_debit_trxn['debit_metadata'], {'airtime': True, 'phone_number': '08031234567', 'network': 'mtn ng vtu'})
        
        # test used card online transaction
        used_your_card_online_debit_trxn = parse_debit_transaction(used_your_card_online_data)
        self.assertEqual(used_your_card_online_debit_trxn['amount'], 1000)
        self.assertEqual(used_your_card_online_debit_trxn['date_of_transaction'], datetime.strptime(transfer_data['date'], "%Y-%m-%d"))
        self.assertEqual(used_your_card_online_debit_trxn['debit_metadata'], {'online_payment': True, 'service_for_online_payment': 'amazon'})
        
        # test used card on pos
        used_card_in_pos_trxn = parse_debit_transaction(used_card_in_pos_data)
        self.assertEqual(used_card_in_pos_trxn['amount'], 1000)
        self.assertEqual(used_card_in_pos_trxn['date_of_transaction'], datetime.strptime(transfer_data['date'], "%Y-%m-%d"))
        self.assertEqual(used_card_in_pos_trxn['debit_metadata'], {'point_of_sale': True})
        
        
    def test_credit_transaction(self):
        transfer_data = {
            "trxn_statement": "John Doe just sent you ₦1,000,000 - Salary. love",
            "date": "2026-01-02"
        }
        
        reversal_data = {
            "trxn_statement": "You tried to make a transfer of ₦1,000,000, and it didn't go through so we've reversed it.".lower(),
            "date": "2026-01-02"
        }
        
        from_savings_data = {
            "trxn_statement": "You took out ₦1,000,000 from your personal savings.".lower(),
            "date": "2026-01-02"
        }
        
        
    
        # test credit by airtime
        transfer_credit_trxn = parse_credit_transaction(transfer_data)
        self.assertEqual(transfer_credit_trxn['amount'], 1000000)
        self.assertEqual(transfer_credit_trxn['date_of_transaction'], datetime.strptime(transfer_data['date'], "%Y-%m-%d"))
        self.assertNotEqual(transfer_credit_trxn['credit_metadata'], {"transfer": True, "sender": "john doe", "narration": "salary"})
        
        # test credit by reversal
        reversal_credit_trxn = parse_credit_transaction(reversal_data)
        self.assertEqual(reversal_credit_trxn['amount'], 1000000)
        self.assertEqual(reversal_credit_trxn['date_of_transaction'], datetime.strptime(reversal_data['date'], "%Y-%m-%d"))
        self.assertEqual(reversal_credit_trxn['credit_metadata'], {"reversal": True})
        
        # test credit by from_savings.
        from_savings_trxn = parse_credit_transaction(from_savings_data)
        self.assertEqual(from_savings_trxn['amount'], 1000000)
        self.assertEqual(from_savings_trxn['date_of_transaction'], datetime.strptime(from_savings_data['date'], "%Y-%m-%d"))
        self.assertEqual(from_savings_trxn['credit_metadata'], {"from_savings": True, "savings_account": "personal"})
        


if __name__ == "__main__":
    unittest.main()