import os
import redis
from redis import Redis
from imap_tools import MailBox, AND, MailboxLoginError
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict
from bs4 import BeautifulSoup
from imap_tools.mailbox import BaseMailBox
from datetime import datetime

from src.credit import (
    get_credit_by_alert_info,
    is_credit_by_reversal,
    is_credit_by_transfer,
    is_credit_by_removal_from_savings,
    get_savings_pocket
)

from src.debit import (
    get_debit_by_airtime_info,
    get_narration_and_receiver,
    get_service_for_online_card_payment,
    is_debit_by_airtime_recharge,
    is_debit_by_card_online,
    is_debit_by_card_pos,
    is_debit_by_spend_and_save,
    is_debit_by_transfer
)

from src.logger import logger

from storage.apis import write_credit_trxn, write_debit_trxn
from storage.base import engine, Base
from utils.utils import get_amount

load_dotenv(find_dotenv())


def redis_conn() -> Redis | None:
    """
    Connects to redis.
    """
    try:
        r = redis.from_url(os.getenv("REDIS_URL"))
        return r
    except Exception as e:
        logger.info(f"failed to connect to redis. the error {e} occurred.")
        return None
        
def login(server, email, password) -> BaseMailBox | None:
    """
    Logs in to the IMAP server.
    """
    try:
        return MailBox(server).login(email, password)
    except MailboxLoginError as e:
        logger.info("failed to login ", str(e))


def parse_debit_transaction(transaction):
    """
    Parses debit transactions.
    """
    trxn_statement = transaction['trxn_statement'].lower()
    
    res = {'date_of_transaction': datetime.strptime(transaction['date'], "%Y-%m-%d")}
    res['amount'] = float(get_amount(trxn_statement).replace(',', ''))
    res['debit_metadata'] = {}
    
    if is_debit_by_airtime_recharge(trxn_statement):
        network = get_debit_by_airtime_info(trxn_statement)['network']
        phone_number = get_debit_by_airtime_info(trxn_statement)['phone_number']
        res['debit_metadata']['airtime'] = True
        res['debit_metadata']['network'] = network
        res['debit_metadata']['phone_number'] = phone_number
    
    if is_debit_by_card_online(trxn_statement):
        service_for_online_payment = get_service_for_online_card_payment(trxn_statement)
        res['debit_metadata']['online_payment'] = True
        res['debit_metadata']['service_for_online_payment'] = service_for_online_payment

    if is_debit_by_card_pos(trxn_statement):
        res['debit_metadata']['point_of_sale'] = True
    
    if is_debit_by_spend_and_save(trxn_statement):
        res['debit_metadata']['savings'] = True
    
    if is_debit_by_transfer(trxn_statement):
        info = get_narration_and_receiver(trxn_statement)
        res['debit_metadata']['transfer'] = True
        res['debit_metadata']['receiver'] = info['receiver']
        res['debit_metadata']['narration'] = info['description']
       
    return res
    
def parse_credit_transaction(transaction):
    """
    Parses credit transactions.
    """
    trxn_statement = transaction['trxn_statement'].lower()
    
    res = {'date_of_transaction': datetime.strptime(transaction['date'], "%Y-%m-%d")}
    res['amount'] = float(get_amount(trxn_statement).replace(',', ''))
    res['credit_metadata'] = {}
    
    if is_credit_by_reversal(trxn_statement):
        res['credit_metadata']['reversal'] = True
    
    if is_credit_by_removal_from_savings(trxn_statement):
        savings_account = get_savings_pocket(trxn_statement)
        res['credit_metadata']['from_savings'] = True
        res['credit_metadata']['savings_account'] = savings_account if savings_account else ""
        
    if is_credit_by_transfer(trxn_statement):
        sender = get_credit_by_alert_info(trxn_statement)['sender']
        narration = get_credit_by_alert_info(trxn_statement)['description']
        res['credit_metadata']['transfer'] = True
        res['credit_metadata']['sender'] = sender
        res['credit_metadata']['narration'] = narration
        
    return res
    
def generally_classify_transactions(transaction) -> str | None:
    """
    Classifies each transaction as credit or debit for easier parsing.
    """
    statement = transaction['trxn_statement'].lower()
    logger.info(f"Transaction statement: {statement}")
    
    # todo: fix bug that classifies both credit and debit transactions as debit because of how "you just sent" and "just sent you" are in both types of transaction. 
    if ("you just sent" in statement
        or "you just recharged" in statement
        or "you used your card online" in statement 
        or "you used your kuda card on a pos" in statement 
        or "you saved some money" in statement
        or "we moved" in statement
    ):
        return "debit"
    
    if ("so we've reversed" in statement 
        or "just sent you" in statement
        or "you took out" in statement
    ):
        return "credit" 
    
    return None

def parse_and_load_transactions_to_db(n: int) -> List[Dict[str, str]] | None:
    """
    Parses and loads transactions into the database.
    """
    server, email, password = os.getenv("IMAP_SERVER"), os.getenv("EMAIL"), os.getenv("PASSWORD")
    imap_client = login(server, email, password) 
    if not imap_client:
        logger.info("could not connect to imap client, check if your environment variables are configured correctly or if your have proper internet connection.")
        return 
    
    batch = imap_client.fetch(criteria=AND(from_=os.getenv("KUDA")), reverse=True)
    debit_trxn_count = credit_trxn_count = invalid_trxn_count = 0
    
    
    r = redis_conn()
    if not r:
        logger.info("failed to connect to redit before parsing transactions.")
        return 
        
    if not r.get("checkpoint"):
        r.set("checkpoint", 0) # if it does not exist, i.e first call, create checkpoint and set it's value to 0
    
    checkpoint = r.get("checkpoint").decode("utf-8") # get checkpoint again.

    for idx, trxn in enumerate(batch):
        if idx < int(checkpoint): # don't double process this transaction.
            logger.info(f"skipping this transaction because transaction {idx} has already been processed and is in the db.")
            continue
        
        if idx == n:  
            logger.info(f"done processing all {n} transactions.")
            break
            
        s = BeautifulSoup(trxn.html, 'html.parser')
        transaction = {
            "trxn_statement": s.span.get_text(),
            "date": datetime.strftime(trxn.date, "%Y-%m-%d")
        }
        trxn_type = generally_classify_transactions(transaction)
        
        if not trxn_type:
            logger.info(f"Transaction number: {idx} is an invalid type of transaction")
            invalid_trxn_count += 1
            
        elif trxn_type == "debit":
            logger.info(f"Transaction number: {idx} is a debit transaction.")
            debit = parse_debit_transaction(transaction)
            logger.info(f"{debit}")
            write_debit_trxn(debit)
            debit_trxn_count += 1 
            logger.info("\n")
        elif trxn_type == "credit":
            logger.info(f"Transaction no: {idx} is a credit transaction.")
            credit = parse_credit_transaction(transaction)
            write_credit_trxn(credit)
            logger.info(f"{credit}")
            credit_trxn_count += 1
            logger.info("\n")
    
    r.set("checkpoint", n if n > int(checkpoint) else int(checkpoint)) # update counter to be the new checkpoint 
    
    logger.info(f"Processed {n - int(checkpoint)} number of transactions.")
    logger.info(f"{debit_trxn_count} of them were debit transactions.")
    logger.info(f"{credit_trxn_count} of them were credit transactions.")
    logger.info(f"{invalid_trxn_count} of them were invalid transactions.")



def create_tables():
    """
    Creates tables in the database.
    """
    logger.info("connecting to db and creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("tables successfully created.")