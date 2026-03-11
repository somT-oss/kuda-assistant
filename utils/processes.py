import re
from datetime import datetime
from src.logger import logger

def process_date_str(date_str):
    original_format = "%a, %d %b %Y %H:%M:%S %z (%Z)"
    date_obj = datetime.strptime(date_str, original_format)
    formatted_date = date_obj.strftime("%Y-%m-%d")

    return formatted_date


def process_date_file_extension(date_str):
    date_object = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z (%Z)')
    formatted_date = date_object.strftime('%Y-%m-%d_%H:%M:%S')

    return formatted_date


def process_date(file_name):
    pattern = r'\d{4}-\d{2}-\d{2}'
    match = re.search(pattern, file_name)
    if match:
        date_str = match.group(0)
        return date_str

def get_amount(transaction_information):
    pattern = r'₦(\d+(?:,\d+)*(?:\.\d{2})?)'
    match = re.search(pattern, transaction_information)
    if match:
        amount = match.group(1)
        return amount
    else:
        raise ValueError("Amount not found.")

def get_start_datetime_end_datetime(start_date, end_date):
    datetime_start_date: datetime
    datetime_end_date: datetime
    
    try:
        datetime_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        datetime_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        return datetime_start_date, datetime_end_date
    except ValueError:
        logger.info(f"Could not convert {start_date} or {end_date} to datetime obj. Incorrect format for {start_date} or {end_date}")
        return None
 