def is_credit_by_alert(transaction_information):
    key_phrase = "just sent you"

    if key_phrase not in transaction_information:
        return False

    return True


def is_credit_by_reversal(transaction_header):
    header_phrase = 'We Reversed Some Money Into Your Account'

    if header_phrase != transaction_header:
        return False
    return True


def get_credit_by_alert_info(transaction_information):
    info = transaction_information
    sender = info[0:(info.index("just") - 1)]
    description = ""
    res = {
        "sender": sender,
        "description": description
    }

    return res

