from datetime import datetime, timedelta

TIMEFRAME_IN_DAYS = 14

START_DATE = (datetime.today() - timedelta(14)).date()
END_DATE = datetime.today().date()

SEEN_FILE_DIRECTORY = f'seen_email_for_{START_DATE.strftime("%B")}-timeframe={START_DATE.day}th-{END_DATE.day}th'
UNSEEN_FILE_DIRECTORY = f'unseen_email_for_{START_DATE.strftime("%B")}-timeframe={START_DATE.day}th-{END_DATE.day}th'
