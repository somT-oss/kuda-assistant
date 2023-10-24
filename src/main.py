import logging
from datetime import date
from dotenv import load_dotenv
from pprint import pprint
import os

import pandas as pd
from bs4 import BeautifulSoup
from imap_tools import MailBox, AND, MailboxLoginError

from src.credit import *
from src.debit import *
from utils.constants import START_DATE, END_DATE, SEEN_FILE_DIRECTORY, UNSEEN_FILE_DIRECTORY

from utils.processes import *

load_dotenv("../.env")


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


def get_messages_details():
    logger.info("Parsing file directory")
    files = os.listdir(SEEN_FILE_DIRECTORY)

    transaction_details = {}
    transaction_holder = []

    for file in files:
        logger.info("Reading html from local storage")
        with open(f'{SEEN_FILE_DIRECTORY}/{file}', 'r') as f:
            html_content = f.read()

        logger.info("Parsing html file with BS4")
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


def process_unseen_messages(con, kuda):
    if con is None:
        return "Could not connect to gmail"

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

            if os.path.exists(UNSEEN_FILE_DIRECTORY) is False:
                logger.info(f"Creating folder directory for month: {date_object.strftime('%B')}...")
                os.mkdir(UNSEEN_FILE_DIRECTORY)

            logger.info("Writing individual transaction history to their respective files...")
            with open(f'{UNSEEN_FILE_DIRECTORY}/transaction_on_{date_object.strftime("%Y-%m-%d")}.html', 'w') as file:
                file.write(email)
                logger.info("Done!")

    conclusion = {
        "total number of unread emails": total_number_of_unseen_messages,
        "total number of unread emails processed in date timeframe": total_number_of_unseen_messages_in_timeframe
    }
    logger.info('----------------------------------DONE WRITING UNREAD EMAILS TO DIR----------------------------------')
    return conclusion


def process_seen_messages(con, kuda):
    if con is None:
        return "Could not connect to gmail"

    mb = con
    logger.info("Getting list of read transactions from Kuda")
    seen_messages = mb.fetch(criteria=AND(seen=True, from_=kuda),
                             mark_seen=False,
                             bulk=True)

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

            if os.path.exists(SEEN_FILE_DIRECTORY) is False:
                logger.info(f"Creating folder directory for month: {date_object.strftime('%B')}...")
                os.mkdir(SEEN_FILE_DIRECTORY)

            logger.info("Writing individual transaction history to their respective files...")
            with open(f'{SEEN_FILE_DIRECTORY}/transaction_on_{date_object.strftime("%Y-%m-%d")}.html', 'w') as file:
                file.write(email)
                logger.info("Done!\n")

    conclusion = {
        "total number of read messages": total_number_of_seen_messages,
        "total number of read messages processed in date timeframe": total_number_of_seen_messages_in_timeframe
    }
    logger.info('----------------------------------DONE WRITING READ EMAILS TO DIR------------------------------------')
    return conclusion


def process_debit(transaction_holder):
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
            res['airtime_recharge'] = 'False'
        else:
            logger.info("Debit is airtime recharge!\n")
            res['airtime_recharge'] = 'True'
            airtime_info = get_debit_by_airtime_info(transaction.get('information'))
            res['network'] = airtime_info.get('network')
            res['phone_number'] = airtime_info.get('phone_number')
            res['amount'] = get_amount(transaction.get('information'))

        logger.info("Checking if debit is by transfer...")
        if is_debit_by_transfer(transaction.get('information')) is not True:
            logger.info("Debit is not by transfer\n")
            res['transfer'] = 'False'
        else:
            logger.info("Debit is by transfer\n")
            res['transfer'] = 'True'
            transfer_info = get_debit_by_alert_info(transaction.get('information'))
            res['amount'] = get_amount(transaction.get('information'))
            res['receiver'] = transfer_info.get('receiver')
            res['description'] = transfer_info.get('description')

        logger.info("Checking if debit is by using card at POS...")
        if is_debit_by_card_pos(transaction.get('header')) is not True:
            logger.info("Debit is not by using card at POS\n")
            res['card_pos_withdrawal'] = 'False'
        else:
            logger.info("Debit is by using card at POS\n")
            res['card'] = 'True'
            res['atm_card'] = 'True'
            res['amount'] = get_amount(transaction.get('information'))

        logger.info("Checking if debit is by using card online...")
        if is_debit_by_card_online(transaction.get('header')) is not True:
            logger.info("Debit is not by using card online\n")
            res['card_online'] = 'False'
        else:
            logger.info("Debit is by using card online\n")
            res['card'] = 'True'
            res['card_online'] = 'True'
            res['amount'] = get_amount(transaction.get('information'))

        logger.info("Checking if debit is savings...")
        if is_debit_by_spend_and_save(transaction.get('information')) is not True:
            logger.info("Debit is not by savings\n")
            res['spend_and_save'] = 'False'
        else:
            logger.info("Debit is by savings\n")
            res['spend_and_save'] = 'True'
            res['amount'] = get_amount(transaction.get('information'))

        res['date'] = transaction.get("date")
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
            res['credit_by_alert'] = 'False'
        else:
            logger.info("Credit is by alert\n")
            res['credit_by_alert'] = 'True'
            amount = get_amount(transaction.get('information'))
            res['amount'] = amount
            alert_info = get_credit_by_alert_info(transaction.get('information'))
            res['sender'] = alert_info.get('sender')
            res['description'] = alert_info.get('description')

        logger.info("Checking if credit is by money reversal")
        if is_credit_by_reversal(transaction.get('header')) is not True:
            logger.info("Credit is not by money reversal\n")
            res['credit_by_reversal'] = 'False'
        else:
            logger.info("Credit is by money reversal\n")
            res['amount'] = get_amount(transaction.get('header'))
            res['credit_by_reversal'] = 'True'

        res['date'] = transaction.get('date')

        logger.info(f"Done processing debit: id = [{no_of_credit_alerts}]")
        logger.info("--------------------------DONE------------------------------------")

        credit_alert.append(res)

    final_res = {
        "credit_alert": credit_alert,
        "no_of_credit_alert": no_of_credit_alerts
    }
    return final_res


def write_debit_to_excel(debit_alert):
    debit_list = debit_alert.get('debit_alert')
    try:
        df = pd.DataFrame(debit_list)
        excel_file = 'debit_for_the_week.xlsx'
        df.to_excel(excel_file, index=False)
        return "Done"
    except Exception as e:
        return f"{e}"


def write_credit_to_excel(credit_alert):
    credit_list = credit_alert.get('credit_alert')
    try:
        df = pd.DataFrame(credit_list)
        excel_file = 'credit_for_the_week.xlsx'
        df.to_excel(excel_file, index=False)
        return "Done"
    except Exception as e:
        return f"{e}"


if __name__ == "__main__":
    SERVER = os.getenv("SERVER")
    USER = os.getenv("GMAIL")
    PASSWORD = os.getenv("PASSWORD")
    KUDA = os.getenv("KUDA")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    conn = connection(SERVER, USER, PASSWORD)
    unseen_email_data = process_unseen_messages(conn, KUDA)
    seen_email_data = process_seen_messages(conn, KUDA)
    email_details = get_messages_details()

    write_debit_alert = process_debit(email_details)
    write_credit_alert = process_credit(email_details)

    pprint(write_debit_alert)
    # write_debit_to_excel(write_debit_alert)
    # write_credit_to_excel(write_credit_alert)
