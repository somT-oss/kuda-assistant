from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

"""
Constants used across the project.
"""

ENV_FILE_PATH = "/home/somto/Dev/accountant/.env"

load_dotenv(dotenv_path=ENV_FILE_PATH, verbose=True)

TIMEFRAME_IN_DAYS = 8

PREFIX_PATH = '..'

START_DATE = (datetime.today() - timedelta(TIMEFRAME_IN_DAYS)).date()
END_DATE = datetime.today().date()

READ_TRANSACTION_RECEIPTS = f'READ_TRANSACTION_RECEIPTS_FOR_{START_DATE.strftime("%B").upper()}:{START_DATE.day}th-{END_DATE.day}th'
UNREAD_TRANSACTION_RECEIPTS = f'UNREAD_TRANSACTION_RECEIPTS_FOR_{START_DATE.strftime("%B").upper()}:{START_DATE.day}th-{END_DATE.day}th'

CREDIT_REPORT_EXCEL = f'credit_report_for_{START_DATE.strftime("%B")}_{START_DATE.day}th-{END_DATE.day}th.xlsx'
DEBIT_REPORT_EXCEL = f'debit_report_for_{START_DATE.strftime("%B")}_{START_DATE.day}th-{END_DATE.day}th.xlsx'

EMAIL_SUBJECT = 'Weekly Transaction Report'
EMAIL_MESSAGE = 'Please find the attached file.'

MONGO_CONNECTION_URI = f"mongodb+srv://{os.getenv('MONGODB_USERNAME')}:{os.getenv('MONGODB_PASSWORD')}@kudaassistantcluster.spowrzp.mongodb.net/?retryWrites=true&w=majority"
DATABASE = 'transactions_db'
