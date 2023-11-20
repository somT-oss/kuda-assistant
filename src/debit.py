def is_debit_by_airtime_recharge(transaction_information):
    """
    Checks to see if debit is by airtime recharge.
    """
    key_phrase = 'You just recharged'

    if key_phrase not in transaction_information:
        return False

    return True


def is_debit_by_transfer(transaction_information):
    """
    Checks to see if debit is by transfer.
    """
    key_phrase = 'You just sent'

    if key_phrase not in transaction_information:
        return False
    return True


def is_debit_by_card_online(transaction_header):
    """
    Checks to see if debit is by use of card online
    """
    header_phrase = 'You Used Your Kuda Card Online'

    if transaction_header != header_phrase:
        return False
    return True


def is_debit_by_card_pos(transaction_header):
    """
    Checks to see if debit is by card at POS or ATM.
    """
    header_phrase = 'You Used Your Kuda Card On A POS'

    if transaction_header != header_phrase:
        return False
    return True


def is_debit_by_spend_and_save(transaction_header):
    """
    Checks to see if debit is by saving through spend and save.
    """
    header_phrase = 'You Saved Some Money'

    if header_phrase != transaction_header:
        return False
    return True


def process_receiver(transaction_information):
    """
    Gets the recipient of the transferred money
    """
    info_list = transaction_information.split("to")
    chunk = info_list[-1]
    money_receiver = chunk[1:(chunk.index('-')-1)]

    return money_receiver


def get_debit_by_alert_info(transaction_information):
    """
    Gets the information of a debit (by transfer)
    """
    info = transaction_information.replace("Love, The Kuda Team.", "")
    receiver = process_receiver(transaction_information)
    description = info[(info.index("-") + 1):(len(info) - 2)]

    res = {
        "receiver": receiver,
        "description": description
    }
    return res


def get_debit_by_airtime_info(transaction_information):
    """
    Gets the information of debit (by airtime recharge)
    """
    info = transaction_information
    first_char = info.index("d") + 2
    network = info[first_char:first_char + 3]
    raw_phone_number = info[(info.index("-") - 14):(info.index("-") - 1)]
    phone_number = raw_phone_number.replace("234", "0")

    res = {
        "network": network,
        "phone_number": phone_number
    }
    return res

