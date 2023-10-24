import re
from datetime import datetime


def process_date_str(date_str):
    # Define the format of the original date string
    original_format = "%a, %d %b %Y %H:%M:%S %z (%Z)"

    # Parse the original date string into a datetime object
    date_obj = datetime.strptime(date_str, original_format)

    # Format the datetime object into the desired "yyyy-mm-dd" format
    formatted_date = date_obj.strftime("%Y-%m-%d")

    return formatted_date


def process_date(file_name):
    pattern = r'\d{4}-\d{2}-\d{2}'
    # Use re.search to find the match
    match = re.search(pattern, file_name)
    if match:
        # Extract the matched date
        date_str = match.group(0)
        return date_str


def get_amount(transaction_information):
    pattern = r'₦(\d+(?:,\d+)*(?:\.\d{2})?)'
    # Define a regex pattern to match the currency symbol (₦) and the amount
    match = re.search(pattern, transaction_information)
    if match:
        # Extract the matched amount
        amount = match.group(1)
        return amount
    else:
        return "Amount not found"
