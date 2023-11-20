import logging
from datetime import date

from dotenv import load_dotenv
import os
from bson.binary import Binary
from io import BytesIO

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from utils.constants import MONGO_CONNECTION_URI

import pandas as pd
from bs4 import BeautifulSoup
from imap_tools import MailBox, AND, MailboxLoginError

from src.credit import *
from src.debit import *

from utils.constants import START_DATE, END_DATE, READ_TRANSACTION_RECEIPTS, UNREAD_TRANSACTION_RECEIPTS, \
    CREDIT_REPORT_EXCEL, \
    DEBIT_REPORT_EXCEL, ENV_FILE_PATH, DATABASE, ABSOLUTE_PATH
from utils.mailer import send_transaction_excel

from utils.processes import *

load_dotenv(dotenv_path=ENV_FILE_PATH, verbose=True)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def connection(server, user, password):
    """
    Establish connection to Gmail
    """
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


def mongo_connection():
    client = None
    try:
        con = MongoClient(MONGO_CONNECTION_URI, server_api=ServerApi('1'))
        if con:
            client = con
        return client
    except Exception as e:
        print(e)


class ReadTransactionProcessor:

    @staticmethod
    def store_read_transactions(transaction, collection):
        email = transaction.html
        encoded_email = email.encode('utf8')
        binary_email = Binary(encoded_email)

        converted_date = process_date_str(transaction.date_str)
        date_object = date.fromisoformat(converted_date)

        if date_object.year != START_DATE.year:
            logger.info(f"Not processing transactions older than: {START_DATE.year}")

        if date_object.month != START_DATE.month:
            logger.info(f"Not processing transactions for: {date_object.strftime('%B')} {date_object.year}\n")

        if START_DATE < date_object <= END_DATE:
            date_extensions = process_date_file_extension(transaction.date_str)

            collection.insert_one({
                "filename": f"transaction_on_{date_extensions}.html",
                "file": binary_email,
                "date_created": str(END_DATE)
            })

    @staticmethod
    def process_read_transactions(transaction):

        binary_receipt = transaction.get('file')
        decoded_receipt = binary_receipt.decode('utf8')
        html_content = BytesIO(decoded_receipt.encode('utf8')).read().decode('utf8')

        logger.info("Parsing html file with BS4 \n")
        soup = BeautifulSoup(html_content, 'html.parser')

        date_str = process_date(transaction.get('filename'))
        header = soup.h1
        information = soup.span

        if header is None or information is None:
            logger.info(
                f"Document with id:{transaction.get('_id')} has an issue with either the header, body or date value")
            logger.info(f"header: {header} "
                        f"information: {information}"
                        )
            logger.info(f"Document with id:{transaction.get('_id')} is not a transactional email\n")
        else:
            return {'id': transaction.get('_id'),
                    'header': header.text,
                    'information': information.text, "date": date_str
                    }


class UnreadTransactionsProcessor:

    @staticmethod
    def store_unread_transactions(transaction, collection):

        email = transaction.html
        encoded_email = email.encode('utf8')
        binary_email = Binary(encoded_email)

        converted_date = process_date_str(transaction.date_str)
        date_object = date.fromisoformat(converted_date)

        if date_object.year != START_DATE.year:
            logger.info(f"Not processing transactions older than: {START_DATE.year}")

        if date_object.month != START_DATE.month:
            logger.info(f"Not processing transactions for: {date_object.strftime('%B')} {date_object.year}\n")

        if START_DATE < date_object <= END_DATE:
            date_extensions = process_date_file_extension(transaction.date_str)

            collection.insert_one({
                "filename": f"transaction_on_{date_extensions}.html",
                "file": binary_email,
                "date_created": str(END_DATE)
            })

    @staticmethod
    def process_unread_transactions(transaction):

        binary_receipt = transaction.get('file')
        decoded_receipt = binary_receipt.decode('utf8')
        html_content = BytesIO(decoded_receipt.encode('utf8')).read().decode('utf8')

        soup = BeautifulSoup(html_content, 'html.parser')

        date_str = process_date(transaction.get('filename'))
        header = soup.h1
        information = soup.span

        if header is None or information is None:
            logger.info(
                f"Document with id:{transaction.get('_id')} has an issue with either the header, body or date value")
            logger.info(f"header: {header} "
                        f"information: {information}"
                        )
            logger.info(f"Document with id:{transaction.get('_id')} is not a transactional email\n")
        else:
            return {'id': transaction.get('_id'),
                    'header': header.text,
                    'information': information.text, "date": date_str
                    }


def scraper(con, mongo_connect, kuda):
    if con is None:
        return {
            "error": f"con return {con}"
        }

    if mongo_connect is None:
        return {
            "error": f"{mongo_connect}"
        }

    db = mongo_connect.get_database(DATABASE)

    if UNREAD_TRANSACTION_RECEIPTS not in db.list_collection_names():
        db.create_collection(UNREAD_TRANSACTION_RECEIPTS)

    if READ_TRANSACTION_RECEIPTS not in db.list_collection_names():
        db.create_collection(READ_TRANSACTION_RECEIPTS)

    read_transaction_collection = db.get_collection(READ_TRANSACTION_RECEIPTS)
    unread_transaction_collection = db.get_collection(UNREAD_TRANSACTION_RECEIPTS)

    mb = con
    seen_transactions = mb.fetch(criteria=AND(seen=True, from_=kuda),
                                 mark_seen=False, bulk=True)
    unseen_transactions = mb.fetch(criteria=AND(seen=False, from_=kuda),
                                   mark_seen=False, bulk=True)

    for transaction in seen_transactions:
        ReadTransactionProcessor.store_read_transactions(transaction, read_transaction_collection)

    for transaction in unseen_transactions:
        UnreadTransactionsProcessor.store_unread_transactions(transaction, unread_transaction_collection)

    logger.info("Done storing both read and unread transactions to mongodb! \n")


def compute_transaction(mongo_connect):
    transaction_list = []

    if mongo_connect is None:
        return {
            "error": f"{mongo_connect}"
        }

    db = mongo_connect.get_database(DATABASE)
    read_transaction_collection = db.get_collection(READ_TRANSACTION_RECEIPTS).find({"date_created": str(END_DATE)})
    unread_transaction_collection = db.get_collection(UNREAD_TRANSACTION_RECEIPTS).find({"date_created": str(END_DATE)})

    for transaction in read_transaction_collection:
        logger.info("Processing read transaction receipts...")
        transaction_list.append(ReadTransactionProcessor.process_read_transactions(transaction))
    logger.info("\n Done processing read transaction \n")

    for transaction in unread_transaction_collection:
        logger.info("Processing unread transaction receipts...")
        transaction_list.append(UnreadTransactionsProcessor.process_unread_transactions(transaction))
    logger.info("\n Done processing unread transaction \n")

    return transaction_list


def process_debit(transaction_holder) -> dict:
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
            res['AMOUNT'] = int(float(get_amount(transaction.get('information').replace(',', ''))))

        logger.info("Checking if debit is by transfer...")
        if is_debit_by_transfer(transaction.get('information')) is not True:
            logger.info("Debit is not by transfer\n")
            res['TRANSFER'] = 'False'
        else:
            logger.info("Debit is by transfer\n")
            res['TRANSFER'] = 'True'
            transfer_info = get_debit_by_alert_info(transaction.get('information'))
            res['AMOUNT'] = int(float(get_amount(transaction.get('information').replace(',', ''))))
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
            res['AMOUNT'] = int(float(get_amount(transaction.get('information').replace(',', ''))))

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
            res['AMOUNT'] = int(float(get_amount(transaction.get('information').replace(',', ''))))

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


def process_credit(transaction_holder):
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
            res['AMOUNT'] = int(float(amount.replace(',', '')))
            alert_info = get_credit_by_alert_info(transaction.get('information'))
            res['SENDER'] = alert_info.get('sender')
            res['DESCRIPTION'] = alert_info.get('description')

        logger.info("Checking if credit is by money reversal")
        if is_credit_by_reversal(transaction.get('header')) is not True:
            logger.info("Credit is not by money reversal\n")
            res['CREDIT BY REVERSAL'] = 'False'
        else:
            logger.info("Credit is by money reversal\n")
            res['AMOUNT'] = int(float(get_amount(transaction.get('header').replace(',', ''))))
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


def write_debit_to_excel(debit_alert) -> str:
    """
    Gets the list of debits, converts it into a dataframe and writes it to an excel file.
    """
    debit_list = debit_alert.get('debit_alert')
    try:
        df = pd.DataFrame(debit_list)
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df.sort_values(by='DATE', ascending=True)
        df.to_excel(f"{ABSOLUTE_PATH}/{DEBIT_REPORT_EXCEL}", index=False)
        return "Done"
    except Exception as e:
        return f"{e}"


def write_credit_to_excel(credit_alert) -> str:
    """
    Gets the list of debits, converts it into a dataframe and writes it to an excel file.
    """
    credit_list = credit_alert.get('credit_alert')
    try:
        df = pd.DataFrame(credit_list)
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df.sort_values(by='DATE', ascending=True)
        df.to_excel(f"{ABSOLUTE_PATH}/{CREDIT_REPORT_EXCEL}", index=False)
        return "Done"
    except Exception as e:
        return f"{e}"


if __name__ == "__main__":
    SERVER = os.getenv("IMAP_SERVER")
    USER = os.getenv("RECEIVER_EMAIL")
    PASSWORD = os.getenv("RECEIVER_PASSWORD")
    KUDA = os.getenv("KUDA")

    conn = connection(SERVER, USER, PASSWORD)
    mongo_con = mongo_connection()

    scraper(conn, mongo_con, KUDA)
    raw_transaction_dict = compute_transaction(mongo_con)

    write_debit_alert = process_debit(raw_transaction_dict)
    write_credit_alert = process_credit(raw_transaction_dict)

    write_debit_to_excel(write_debit_alert)
    write_credit_to_excel(write_credit_alert)

    send_transaction_excel()

    logger.info("Successfully sent credit and debit alert transactions")
