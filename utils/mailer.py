import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import os
from dotenv import load_dotenv

from utils.constants import DEBIT_REPORT_EXCEL, CREDIT_REPORT_EXCEL, EMAIL_SUBJECT, EMAIL_MESSAGE, PREFIX_PATH, \
    ENV_FILE_PATH

load_dotenv(dotenv_path=ENV_FILE_PATH, verbose=True)


sender = os.getenv("SENDER_EMAIL")
receiver = os.getenv("RECEIVER_EMAIL")
password = os.getenv("SENDER_PASSWORD")
smtp_server = os.getenv("SMTP_SERVER")


def send_transaction_excel():
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = EMAIL_SUBJECT

    msg.attach(MIMEText(EMAIL_MESSAGE, 'plain'))

    with open(f'{PREFIX_PATH}/{DEBIT_REPORT_EXCEL}', 'rb') as file:
        attachment = MIMEApplication(file.read(), _subtype="xlsx")
        attachment.add_header('content-disposition', 'attachment', filename=DEBIT_REPORT_EXCEL)
        msg.attach(attachment)

    with open(f'{PREFIX_PATH}/{CREDIT_REPORT_EXCEL}', 'rb') as file:
        attachment2 = MIMEApplication(file.read(), _subtype="xlsx")
        attachment2.add_header('content-disposition', 'attachment', filename=CREDIT_REPORT_EXCEL)
        msg.attach(attachment2)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port=465, context=context) as connection:
        connection.login(user=sender, password=password)
        connection.sendmail(from_addr=sender, to_addrs=receiver,
                            msg=msg.as_string())

