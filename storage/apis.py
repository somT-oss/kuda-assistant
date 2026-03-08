from storage.base import Session
from storage.models import DebitTransaction, CreditTransaction
from src.logger import logger

def write_debit_trxn(debit_trxn_dict) -> None:
    with Session() as session:
        try:
            logger.info("Writing debit transaction to the database...")
            debit_trxn = DebitTransaction()
            debit_trxn.amount = debit_trxn_dict["amount"]
            debit_trxn.date_of_transaction = debit_trxn_dict["date_of_transaction"]
            
            if debit_trxn_dict.get("debit_metadata", {}).get("airtime"):
                debit_trxn.airtime = debit_trxn_dict["debit_metadata"]["airtime"]
                debit_trxn.phone_number = debit_trxn_dict["debit_metadata"]["phone_number"]
                debit_trxn.network = debit_trxn_dict["debit_metadata"]["network"]
            
            if debit_trxn_dict.get("debit_metadata", {}).get("savings"):
                debit_trxn.savings = debit_trxn_dict["debit_metadata"]["savings"]
            
            if debit_trxn_dict.get("debit_metadata", {}).get("point_of_sale"):
                debit_trxn.point_of_sale = debit_trxn_dict["debit_metadata"]["point_of_sale"]
            
            if debit_trxn_dict.get("debit_metadata", {}).get('online_payment'):
                debit_trxn.online_payment = debit_trxn_dict['debit_metadata']['online_payment']
                debit_trxn.service_for_online_payment = debit_trxn_dict['debit_metadata']['service_for_online_payment']
                
            if  debit_trxn_dict.get("debit_metadata", {}).get("transfer"):
                debit_trxn.transfer = debit_trxn_dict["debit_metadata"]["transfer"]
                debit_trxn.receiver = debit_trxn_dict["debit_metadata"]["receiver"]
                debit_trxn.narration = debit_trxn_dict["debit_metadata"]["narration"]
            
            session.add(debit_trxn)
            session.commit()
            logger.info("Successfully wrote debit transaction to the db")
            
        except Exception as e:
            session.rollback()
            logger.info(f"An error occurred: {str(e)}")


def write_credit_trxn(credit_trxn_dict) -> None:
    with Session() as session:
        try:
            logger.info("Writing credit transaction to the database...")
            credit_trxn = CreditTransaction()
            credit_trxn.amount = credit_trxn_dict["amount"]
            credit_trxn.date_of_transaction = credit_trxn_dict["date_of_transaction"]
            
            if credit_trxn_dict.get("credit_metadata", {}).get("transfer"):
                credit_trxn.transfer = credit_trxn_dict["credit_metadata"]["transfer"]
                credit_trxn.sender = credit_trxn_dict["credit_metadata"]["sender"]
                credit_trxn.narration = credit_trxn_dict["credit_metadata"]["narration"]
            if credit_trxn_dict.get("credit_metadata", {}).get("reversal"):
                credit_trxn.reversal = credit_trxn_dict["credit_metadata"]["reversal"]
            if credit_trxn_dict.get("credit_metadata", {}).get("from_savings"):
                credit_trxn.from_savings = credit_trxn_dict.get("credit_metadata", {}).get("from_savings")
                credit_trxn.savings_account = credit_trxn_dict.get("credit_metadata", {}).get("savings_account")
            session.add(credit_trxn)
            session.commit()
            logger.info("Successfully wrote credit transaction to the db")
            
        except Exception as e:
            session.rollback()
            logger.info(f"An error occurred: {e}")
            
                
    