import re

def is_debit_by_airtime_recharge(trxn_statement):
    """
    Checks to see if debit is by airtime recharge.
    """
    if "you just recharged" in trxn_statement:
        return True
    return False

def is_debit_by_transfer(trxn_statement):
    """
    Checks to see if debit is by transfer.
    """
    if "you just sent" in trxn_statement:
        return True
    return False


def is_debit_by_card_online(trxn_statement):
    """
    Checks to see if debit is by use of card online
    """
    if "with your kuda card" in trxn_statement:
        return True
    return False

def get_service_for_online_card_payment(trxn_statement) -> str | None:
    pattern = r"you paid ₦?([\d,.]+) with your kuda card on (.*?)\."
    match = re.search(pattern, trxn_statement, re.IGNORECASE)
    
    if not match:
        return None
    return match.group(2)

def is_debit_by_card_pos(trxn_statement):
    """
    Checks to see if debit is by card at POS or ATM.
    """
    if "you used your card on a pos" in trxn_statement:
        return True
    return False

def is_debit_by_spend_and_save(trxn_statement):
    if "we moved" in trxn_statement:
        return True
    return False

def get_savings_pocket(trxn_statement) -> str | None:
    pattern = r"we moved ₦?([\d,.]+) from your spend account to (.*?) savings"
    match = re.search(pattern, trxn_statement, re.IGNORECASE)
    
    if not match:
        return None
    return match.group(2)
    
def get_narration_and_receiver(trxn_statement):
    """
    Gets the information of a debit (by transfer)
    """
    pattern = r"you just sent ₦?([\d,.]+) to (.*?)\s*-\s*(.*?)\s*\.\s*love"
    match = re.search(pattern, trxn_statement, re.IGNORECASE)
    if not match:
        return None
    return {
        "receiver": match.group(2),
        "description": match.group(3)
    }


def get_debit_by_airtime_info(trxn_statement):
    """
    Gets the information of debit (by airtime recharge)
    """
    pattern = r"you just recharged (.*?)(?:\s+data|\s+airtime)?\s+(\d+) - .*? with ₦?([\d,.]+)"
    match = re.search(pattern, trxn_statement, re.IGNORECASE)
    
    if not match:
        return None
    return {
        "network": match.group(1),
        "phone_number": match.group(2)
    }
        