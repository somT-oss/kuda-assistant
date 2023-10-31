import logging
from datetime import date
from dotenv import load_dotenv
import os
import shutil

import pandas as pd
from bs4 import BeautifulSoup
from imap_tools import MailBox, AND, MailboxLoginError

from src.credit import *
from src.debit import *
from utils.constants import START_DATE, END_DATE, SEEN_FILE_DIRECTORY, UNSEEN_FILE_DIRECTORY, CREDIT_REPORT_EXCEL, \
    DEBIT_REPORT_EXCEL, ENV_FILE_PATH, PREFIX_PATH
from utils.mailer import send_transaction_excel

from utils.processes import *

load_dotenv(dotenv_path=ENV_FILE_PATH, verbose=True)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

"""
Establish connection to Gmail
"""


def connection(server, user, password):
    con = None
    try:
        logger.info("Trying to connect to gmail")
        mb = MailBox(server).login(user, password)
        if mb:
            con = mb
            logger.info("Connection successful")
            return con
    except MailboxLoginError as e:
        logger.error(e)
        return con


"""
Scrapes Gmail for unread emails from kuda.

It also creates a directory 'unseen_email_for_{start_date}th-{end_date}th'. This directory will hold the email responses 
from kuda from the specified start date to the specified end date.

The return dictionary contains the total number of unread emails from kuda of all time and the total number of unread 
emails from the specified start date to the end date.
"""


def process_unseen_messages(con, kuda) -> dict:
    if con is None:
        return {
            "error": f"con return {con}"
        }

    mb = con
    logger.info("Getting list of unread transactions from Kuda")
    unseen_messages = mb.fetch(criteria=AND(seen=False, from_=kuda),
                               mark_seen=False,
                               bulk=True)
    total_number_of_unseen_messages = 0
    total_number_of_unseen_messages_in_timeframe = 0

    for message in unseen_messages:
        email = message.html
        total_number_of_unseen_messages += 1

        converted_date = process_date_str(message.date_str)
        date_object = date.fromisoformat(converted_date)

        if date_object.year != START_DATE.year:
            logger.info(f"Not processing transactions older than: {START_DATE.year}")

        if date_object.month != START_DATE.month:
            logger.info(f"Not processing transactions for: {date_object.strftime('%B')} {date_object.year}\n")

        if START_DATE < date_object <= END_DATE:
            total_number_of_unseen_messages_in_timeframe += 1

            date_extensions = process_date_file_extension(message.date_str)

            if os.path.exists(f"../{UNSEEN_FILE_DIRECTORY}") is False:
                logger.info(f"Creating folder directory for month: {date_object.strftime('%B')}...")
                os.mkdir(f"../{UNSEEN_FILE_DIRECTORY}")

            logger.info("Writing individual transaction history to their respective files...")
            with open(f'../{UNSEEN_FILE_DIRECTORY}/transaction_on_{date_extensions}.html', 'w') as file:
                file.write(email)
                logger.info("Done!")

    conclusion = {
        "total number of unread emails": total_number_of_unseen_messages,
        "total number of unread emails processed in date timeframe": total_number_of_unseen_messages_in_timeframe
    }
    logger.info('----------------------------------DONE WRITING UNREAD EMAILS TO DIR----------------------------------')
    return conclusion


"""
Scrapes Gmail for read emails from kuda.

It also creates a directory 'seen_email_for_{start_date}th-{end_date}th'. This directory will hold the email responses 
from kuda from the specified start date to the specified end date.

The return dictionary contains the total number of read emails from kuda of all time and the total number of read 
emails from the specified start date to the end date.
"""


def process_seen_messages(con, kuda) -> dict:
    if con is None:
        return {
            "error": f"con returned {con}"
        }

    mb = con
    logger.info("Getting list of read transactions from Kuda")
    seen_messages = mb.fetch(criteria=AND(seen=True, from_=kuda),
                             mark_seen=False, bulk=True)

    total_number_of_seen_messages = 0
    total_number_of_seen_messages_in_timeframe = 0

    for message in seen_messages:
        email = message.html
        total_number_of_seen_messages += 1

        converted_date = process_date_str(message.date_str)
        date_object = date.fromisoformat(converted_date)

        if date_object.year != START_DATE.year:
            logger.info(f"Not processing transactions older than: {START_DATE.year}")

        if date_object.month != START_DATE.month:
            logger.info(f"Not processing transactions for: {date_object.strftime('%B')} {date_object.year}\n")

        if START_DATE < date_object <= END_DATE:
            total_number_of_seen_messages_in_timeframe += 1

            date_extensions = process_date_file_extension(message.date_str)

            if os.path.exists(f"../{SEEN_FILE_DIRECTORY}") is False:
                logger.info(f"Creating folder directory for month: {date_object.strftime('%B')}...")
                os.mkdir(f"../{SEEN_FILE_DIRECTORY}")

            logger.info("Writing individual transaction history to their respective files...")
            with open(f'../{SEEN_FILE_DIRECTORY}/transaction_on_{date_extensions}.html', 'w') as file:
                file.write(email)
                logger.info("Done!\n")

    conclusion = {
        "total number of read messages": total_number_of_seen_messages,
        "total number of read messages processed in date timeframe": total_number_of_seen_messages_in_timeframe
    }
    logger.info('----------------------------------DONE WRITING READ EMAILS TO DIR------------------------------------')
    return conclusion


"""
Reads the html files stored in the seen_email_... folder created.

It converts the html files into a dictionary with three distinct values: header, information and date.

The header contains the header of the mail from the html file.
The information contains the body of the mail from the html file.
The date is the date the email was sent
"""


def get_seen_messages_details() -> list:
    if os.path.exists(f"../{SEEN_FILE_DIRECTORY}") is not True:
        return [{
            "error": f"Folder {SEEN_FILE_DIRECTORY} does not exist"
        }]

    logger.info(f"Parsing files from {SEEN_FILE_DIRECTORY}")
    files = os.listdir(f"../{SEEN_FILE_DIRECTORY}")

    transaction_details = {}
    transaction_holder = []

    for file in files:
        logger.info("Reading html from local storage")
        with open(f'../{SEEN_FILE_DIRECTORY}/{file}', 'r') as f:
            html_content = f.read()

        logger.info("Parsing html file with BS4 \n")
        soup = BeautifulSoup(html_content, 'html.parser')

        date_str = process_date(file)
        header = soup.h1
        information = soup.span

        if header is None or information is None:
            logger.info(f"file: {f.name} has an issue with either the header, body or date value")
            logger.info(f"header: {header} "
                        f"information: {information} "
                        )
            logger.info(f"This means file:{f.name} is not a transactional email\n")
        else:
            transaction_details = {'header': header.text, 'information': information.text, "date": date_str}
        transaction_holder.append(transaction_details)

    return transaction_holder


"""
Reads the html files stored in the unseen_email_... folder created.

It converts the html files into a dictionary with three distinct values: header, information and date.

The header contains the header of the mail from the html file.
The information contains the body of the mail from the html file.
The date is the date the email was sent
"""


def get_unseen_messages_details() -> list:
    if os.path.exists(f"../{UNSEEN_FILE_DIRECTORY}") is not True:
        return [{
            "error": f"Folder {UNSEEN_FILE_DIRECTORY} does not exist"
        }]

    logger.info(f"Parsing file from {UNSEEN_FILE_DIRECTORY}")
    files = os.listdir(f"../{UNSEEN_FILE_DIRECTORY}")

    transaction_details = {}
    transaction_holder = []

    for file in files:
        logger.info("Reading html from local storage")
        with open(f'../{UNSEEN_FILE_DIRECTORY}/{file}', 'r') as f:
            html_content = f.read()

        logger.info("Parsing html file with BS4 \n")
        soup = BeautifulSoup(html_content, 'html.parser')

        date_str = process_date(file)
        header = soup.h1
        information = soup.span

        if header is None or information is None:
            logger.info(f"file: {f.name} has an issue with either the header, body or date value")
            logger.info(f"header: {header} "
                        f"information: {information} "
                        )
            logger.info(f"This means file:{f.name} is not a transactional email\n")
        else:
            transaction_details = {'header': header.text, 'information': information.text, "date": date_str}
        transaction_holder.append(transaction_details)

    return transaction_holder


"""
Processes the data gathered from processing the emails into debits and also categorizes it into different forms of
debit alerts. 
The methods of debit method implemented include: 
 - AIRTIME RECHARGE
 - TRANSFER
 - SPEND AND SAVE
 - CARD USAGE (ONLINE, ATM OR POS)
Returns a dictionary containing a list of dictionaries containing the parsed debits and the number of debits.
 {
   "debit_alerts": debit_alerts --> [list of parsed debits],
   "no_of_debits": no_of_debits --> int(number of debits)
 }
"""


def process_debit(transaction_holder) -> dict:
    logger.info("Initializing debit alert holder list")
    debit_alert = []

    no_of_debit_alerts = 0
    for transaction in transaction_holder:
        res = {}

        logger.info(f"Processing debit: id = [{no_of_debit_alerts}]")
        logger.info("--------------------------START------------------------------------")

        logger.info("Checking if debit is by airtime recharge...")
        if is_debit_by_airtime_recharge(transaction.get('information')) is not True:
            logger.info("Debit is not by airtime recharge\n")
            res['AIRTIME RECHARGE'] = 'False'
        else:
            logger.info("Debit is airtime recharge!\n")
            res['AIRTIME RECHARGE'] = 'True'
            airtime_info = get_debit_by_airtime_info(transaction.get('information'))
            res['NETWORK'] = airtime_info.get('network')
            res['PHONE NUMBER'] = airtime_info.get('phone_number')
            res['AMOUNT'] = get_amount(transaction.get('information'))

        logger.info("Checking if debit is by transfer...")
        if is_debit_by_transfer(transaction.get('information')) is not True:
            logger.info("Debit is not by transfer\n")
            res['TRANSFER'] = 'False'
        else:
            logger.info("Debit is by transfer\n")
            res['TRANSFER'] = 'True'
            transfer_info = get_debit_by_alert_info(transaction.get('information'))
            res['AMOUNT'] = get_amount(transaction.get('information'))
            res['RECEIVER'] = transfer_info.get('receiver')
            res['DESCRIPTION'] = transfer_info.get('description')

        logger.info("Checking if debit is by using card at POS...")
        if is_debit_by_card_pos(transaction.get('header')) is not True:
            logger.info("Debit is not by using card at POS\n")
            res['CARD POS WITHDRAWAL'] = 'False'
        else:
            logger.info("Debit is by using card at POS\n")
            res['CARD'] = 'True'
            res['ATM CARD'] = 'True'
            res['AMOUNT'] = get_amount(transaction.get('information'))

        logger.info("Checking if debit is by using card online...")
        if is_debit_by_card_online(transaction.get('header')) is not True:
            logger.info("Debit is not by using card online\n")
            res['CARD ONLINE'] = 'False'
        else:
            logger.info("Debit is by using card online\n")
            res['CARD'] = 'True'
            res['CARD ONLINE'] = 'True'
            res['AMOUNT'] = get_amount(transaction.get('information'))

        logger.info("Checking if debit is savings...")
        if is_debit_by_spend_and_save(transaction.get('header')) is not True:
            logger.info("Debit is not by savings\n")
            res['SPEND AND SAVE'] = 'False'
        else:
            logger.info("Debit is by savings\n")
            res['SPEND AND SAVE'] = 'True'
            res['AMOUNT'] = get_amount(transaction.get('information'))

        res['DATE'] = transaction.get("date")
        no_of_debit_alerts += 1

        logger.info(f"Done processing debit: id = [{no_of_debit_alerts}]")
        logger.info("--------------------------DONE------------------------------------")

        debit_alert.append(res)

    final_res = {
        "debit_alert": debit_alert,
        "no_of_debit_alert": no_of_debit_alerts
    }
    return final_res


"""
Processes the data gathered from processing the emails into credits and also categorizes it into different forms of
credit alerts. 
The methods of credit method implemented include: 
 - TRANSFER
 - MONEY REVERSAL
Returns a dictionary containing a list of dictionaries containing the parsed credits and the number of debits.
 {
   "debit_alerts": debit_alerts --> [list of parsed debits],
   "no_of_debits": no_of_debits --> int(number of debits)
 }
"""


def process_credit(transaction_holder):
    logger.info("Initializing credit alert holder list")
    credit_alert = []

    no_of_credit_alerts = 0
    for transaction in transaction_holder:

        res = {}

        logger.info(f"Processing debit: id = [{no_of_credit_alerts}]")
        logger.info("--------------------------START------------------------------------")

        logger.info("Checking if credit is by alert")
        if is_credit_by_alert(transaction.get('information')) is not True:
            logger.info("Credit is not by alert\n")
            res['CREDIT BY ALERT'] = 'False'
        else:
            logger.info("Credit is by alert\n")
            res['CREDIT BY ALERT'] = 'True'
            amount = get_amount(transaction.get('information'))
            res['AMOUNT'] = amount
            alert_info = get_credit_by_alert_info(transaction.get('information'))
            res['SENDER'] = alert_info.get('sender')
            res['DESCRIPTION'] = alert_info.get('description')

        logger.info("Checking if credit is by money reversal")
        if is_credit_by_reversal(transaction.get('header')) is not True:
            logger.info("Credit is not by money reversal\n")
            res['CREDIT BY REVERSAL'] = 'False'
        else:
            logger.info("Credit is by money reversal\n")
            res['AMOUNT'] = get_amount(transaction.get('header'))
            res['CREDIT BY REVERSAL'] = 'True'

        res['DATE'] = transaction.get('date')

        logger.info(f"Done processing debit: id = [{no_of_credit_alerts}]")
        logger.info("--------------------------DONE------------------------------------")

        credit_alert.append(res)

    final_res = {
        "credit_alert": credit_alert,
        "no_of_credit_alert": no_of_credit_alerts
    }
    return final_res


"""
Gets the list of debits, converts it into a dataframe and writes it to an excel file.
"""


def write_debit_to_excel(debit_alert) -> str:
    debit_list = debit_alert.get('debit_alert')
    print(debit_list)
    try:
        df = pd.DataFrame(debit_list)
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df.sort_values(by='DATE', ascending=True)
        df.to_excel(f"{PREFIX_PATH}/{DEBIT_REPORT_EXCEL}", index=False)
        return "Done"
    except Exception as e:
        return f"{e}"


"""
Gets the list of debits, converts it into a dataframe and writes it to an excel file.
"""


def write_credit_to_excel(credit_alert) -> str:
    credit_list = credit_alert.get('credit_alert')
    try:
        df = pd.DataFrame(credit_list)
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df.sort_values(by='DATE', ascending=True)
        df.to_excel(f"{PREFIX_PATH}/{CREDIT_REPORT_EXCEL}", index=False)
        return "Done"
    except Exception as e:
        return f"{e}"


"""
Deletes any files and folders created.
"""


def clean_up():
    logger.info("Cleaning up generated files/directories...")

    if os.path.exists(f"{PREFIX_PATH}/{SEEN_FILE_DIRECTORY}"):
        shutil.rmtree(f"{PREFIX_PATH}/{SEEN_FILE_DIRECTORY}")
        logger.info(f"Deleted {SEEN_FILE_DIRECTORY}")
    else:
        logger.info(f"Directory: {SEEN_FILE_DIRECTORY} not found")

    if os.path.exists(f"{PREFIX_PATH}/{UNSEEN_FILE_DIRECTORY}"):
        shutil.rmtree(f"{PREFIX_PATH}/{UNSEEN_FILE_DIRECTORY}")
        logger.info(f"Deleted {UNSEEN_FILE_DIRECTORY}")
    else:
        logger.info(f"Directory: {UNSEEN_FILE_DIRECTORY} not found")

    if os.path.exists(f"{PREFIX_PATH}/{CREDIT_REPORT_EXCEL}"):
        os.remove(f"{PREFIX_PATH}/{CREDIT_REPORT_EXCEL}")
        logger.info(f"Deleted {CREDIT_REPORT_EXCEL}")
    else:
        logger.info(f"File: {CREDIT_REPORT_EXCEL} not found")

    if os.path.exists(f"{PREFIX_PATH}/{DEBIT_REPORT_EXCEL}") is False:
        return f"File: {DEBIT_REPORT_EXCEL} not found"
    os.remove(f"{PREFIX_PATH}/{DEBIT_REPORT_EXCEL}")
    logger.info(f"Deleted {DEBIT_REPORT_EXCEL}")


if __name__ == "__main__":
    SERVER = os.getenv("IMAP_SERVER")
    USER = os.getenv("RECEIVER_EMAIL")
    PASSWORD = os.getenv("RECEIVER_PASSWORD")
    KUDA = os.getenv("KUDA")

    conn = connection(SERVER, USER, PASSWORD)

    unseen_email_data = process_unseen_messages(conn, KUDA)
    seen_email_data = process_seen_messages(conn, KUDA)

    seen_mail_details = get_seen_messages_details()
    unseen_mail_details = get_unseen_messages_details()

    print(seen_mail_details)
    print(unseen_mail_details)

    if seen_mail_details[0].get("error") is None:
        write_debit_alert = process_debit(unseen_mail_details)
        write_credit_alert = process_credit(unseen_mail_details)

        print(write_debit_to_excel(write_debit_alert))
        write_credit_to_excel(write_credit_alert)

        send_transaction_excel()

    if unseen_mail_details[0].get("error") is None:
        write_debit_alert = process_debit(seen_mail_details)
        write_credit_alert = process_credit(seen_mail_details)

        print(write_debit_to_excel(write_debit_alert))
        write_credit_to_excel(write_credit_alert)

        send_transaction_excel()

    if unseen_mail_details[0].get("error") and seen_mail_details[0].get("error") is not None:
        merged_mail_details = seen_mail_details + unseen_mail_details

        write_debit_alert = process_debit(merged_mail_details)
        write_credit_alert = process_credit(merged_mail_details)

        print(write_debit_to_excel(write_debit_alert))
        write_credit_to_excel(write_credit_alert)

        send_transaction_excel()

    """
    Uncomment the clean up method to clean up generated files and directories
    """
    # clean_up()

    logger.info("Successfully sent credit and debit alert transactions")
