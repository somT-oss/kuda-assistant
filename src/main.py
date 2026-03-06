import os
import logging
from imap_tools import MailBox, AND, MailboxLoginError
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict
from bs4 import BeautifulSoup
from imap_tools.mailbox import BaseMailBox
from datetime import datetime

from src.credit import (
    get_credit_by_alert_info,
    is_credit_by_reversal,
    is_credit_by_transfer
)

from src.debit import (
    get_debit_by_airtime_info,
    get_narration,
    is_debit_by_airtime_recharge,
    is_debit_by_card_online,
    is_debit_by_card_pos,
    is_debit_by_spend_and_save,
    is_debit_by_transfer, process_receiver
)

from utils.processes import get_amount


load_dotenv(find_dotenv())

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def login(server, email, password) -> BaseMailBox | None:
    try:
        return MailBox(server).login(email, password)
    except MailboxLoginError as e:
        logger.info("failed to login ", str(e))


def parse_debit_transaction(transaction):
    txn_statement = transaction['trxn_statement']
    
    res = {"date": transaction['date']}
    res['debit'] = True
    res['amount'] = get_amount(txn_statement)
    res['debit_metadata'] = {}
    
    if is_debit_by_airtime_recharge(txn_statement):
        network = get_debit_by_airtime_info(txn_statement)['network']
        phone_number = get_debit_by_airtime_info(txn_statement)['phone_number']
        res['debit_metadata']['airtime'] = True
        res['debit_metadata']['network'] = network
        res['debit_metadata']['phone_number'] = phone_number
    
    if is_debit_by_card_online(txn_statement):
        res['debit_metadata']['card_payment'] = True

    if is_debit_by_card_pos(txn_statement):
        res['debit_metadata']['point_of_sale'] = True
    
    if is_debit_by_spend_and_save(txn_statement):
        res['debit_metadata']['savings'] = True
    
    if is_debit_by_transfer(txn_statement):
        receiver = process_receiver(txn_statement)
        narration = get_narration(txn_statement)
        res['debit_metadata']['receiver'] = receiver
        res['debit_metadata']['transfer'] = True
        res['debit_metadata']['narration'] = narration['description']
       
    return res
    
def parse_credit_transaction(transaction):
    txn_statement = transaction['trxn_statement']
    
    res = {'date': transaction['date']}
    res['amount'] = get_amount(txn_statement)
    res['credit_metadata'] = {}
    
    if is_credit_by_reversal(txn_statement):
        res['credit'] = True
        res['credit_metadata']['reversal'] = True
    
    if is_credit_by_transfer(txn_statement):
        res['credit'] = True
        sender = get_credit_by_alert_info(txn_statement)['sender']
        description = get_credit_by_alert_info(txn_statement)['description']
        res['credit_metadata']['transfer'] = True
        res['credit_metadata']['sender'] = sender
        res['credit_metadata']['description'] = description
        
    return res
    
def generally_classify_transactions(transaction) -> str | None:
    statement = transaction['trxn_statement'].lower()
    
    # todo: fix bug that classifies both credit and debit transactions as debit because of how "you just sent" and "just sent you" are in both types of transaction. 
    if "you just sent" or "you just recharged" or "you used your card online" or "you used your kuda card on a pos" or "you saved some money" in statement:
        return "debit"
    
    if "we reversed some money into your account" or "just sent you" in statement:
        return "credit" 
    
    return None

def unparsed_transactions() -> List[Dict[str, str]] | None:
    server, email, password = os.getenv("IMAP_SERVER"), os.getenv("EMAIL"), os.getenv("PASSWORD")
    imap_client = login(server, email, password) 
    if not imap_client:
        return 
    
    batch = imap_client.fetch(criteria=AND(seen=True, from_=os.getenv("KUDA")), reverse=True)
    counter = debit_trxn_count = credit_trxn_count= 0
    
    for trxn in batch:
        if counter == 99:
            break
        s = BeautifulSoup(trxn.html, 'html.parser')
        transaction = {
            "trxn_statement": s.span.get_text(),
            "date": datetime.strftime(trxn.date, "%Y-%m-%d")
        }
        trxn_type = generally_classify_transactions(transaction)
        
        if not trxn_type:
            logger.info(f"Transaction number: {counter} is an invalid type of transaction")
        
        elif trxn_type == "debit":
            parse_debit_transaction(transaction)
            logger.info(f"Transaction number: {counter} is a debit transaction.")
            debit_trxn_count += 1 
        elif trxn_type == "credit":
            logger.info(f"Transaction no: {counter} is a credit transaction.")
            parse_credit_transaction(transaction)
            debit_trxn_count += 1
        counter += 1 
    
    logger.info(f"Processed {counter} number of transactions.")
    logger.info(f"{debit_trxn_count} of them were debit transactions.")
    logger.info(f"{credit_trxn_count} of them were credit transactions.")

unparsed_transactions()


# store the information to a database using sqlalchemy.


# get data
# 1. check the database to see if data exists
# 1a. if it exists, return it.
# 1b. if it does not, reinitialize with timeframe delta of what the closest date-range in db and fetch from the scraper again.

# update:
# NO! YOU CAN'T UPDATE TRANSACTIONS THAT ALREADY EXISTS.

