import re

def is_credit_by_transfer(transaction_information):
    """
    Checks to see if the credit is by transfer/alert.
    """
    key_phrase = "just sent you"

    if key_phrase not in transaction_information:
        return False

    return True


def is_credit_by_reversal(trxn_statement):
    """
    Checks to see if credits is by reversal.
    """
    if "so we've reversed" in trxn_statement:
        return True
    return False 

def is_credit_by_removal_from_savings(trxn_statement) -> bool:
    if "you took out" in trxn_statement:
        return True
    return False

def get_savings_pocket(trxn_statement) -> str | None:
    match = re.search(r"you took out ₦?([\d,.]+) from your (.*?) savings", trxn_statement, re.IGNORECASE)
    if not match:
        return None
    return match.group(2)

def get_credit_by_alert_info(transaction_information):
    info = transaction_information
    sender = info[0:(info.index("just") - 1)]
    description = ""
    res = {
        "sender": sender,
        "description": description
    }

    return res
