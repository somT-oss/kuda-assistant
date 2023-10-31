from datetime import datetime, timedelta

"""
Constants used across the project.
"""

TIMEFRAME_IN_DAYS = 8

PREFIX_PATH = '..'

START_DATE = (datetime.today() - timedelta(TIMEFRAME_IN_DAYS)).date()
END_DATE = datetime.today().date()

SEEN_FILE_DIRECTORY = f'seen_email_for_{START_DATE.strftime("%B")}-timeframe={START_DATE.day}th-{END_DATE.day}th'
UNSEEN_FILE_DIRECTORY = f'unseen_email_for_{START_DATE.strftime("%B")}-timeframe={START_DATE.day}th-{END_DATE.day}th'

CREDIT_REPORT_EXCEL = f'credit_report_for_{START_DATE.strftime("%B")}_{START_DATE.day}th-{END_DATE.day}th.xlsx'
DEBIT_REPORT_EXCEL = f'debit_report_for_{START_DATE.strftime("%B")}_{START_DATE.day}th-{END_DATE.day}th.xlsx'

EMAIL_SUBJECT = 'Weekly Transaction Report'
EMAIL_MESSAGE = 'Please find the attached file.'

ENV_FILE_PATH = "/home/somto/Dev/accountant/.env"
