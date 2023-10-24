def is_debit_by_airtime_recharge(transaction_information):
    key_phrase = 'You just recharged'

    if key_phrase not in transaction_information:
        return False

    return True


def is_debit_by_transfer(transaction_information):
    key_phrase = 'You just sent'

    if key_phrase not in transaction_information:
        return False
    return True


def is_debit_by_card_online(transaction_information):
    key_phrase = 'You just paid'

    if key_phrase not in transaction_information:
        return False
    return True


def is_debit_by_card_pos(transaction_header):
    header_phrase = 'You Used Your Kuda Card On A POS'

    if transaction_header != header_phrase:
        return False
    return True


def is_debit_by_spend_and_save(transaction_header):
    header_phrase = 'You Saved Some Money'

    if header_phrase != transaction_header:
        return False
    return True


def process_receiver(transaction_information):
    info_list = transaction_information.split("to")
    chunk = info_list[-1]
    money_receiver = chunk[1:chunk.index('-')]

    return money_receiver


def get_debit_by_alert_info(transaction_information):
    info = transaction_information.replace("Love, The Kuda Team.", "")
    receiver = process_receiver(transaction_information)
    description = info[(info.index("-") + 2):(len(info) - 3)]

    res = {
        "receiver": receiver,
        "description": description
    }
    return res


def get_debit_by_airtime_info(transaction_information):
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

