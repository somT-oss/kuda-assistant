from typing import List
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import pandas as pd
from src.logger import logger
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import ssl
import os
import shutil


load_dotenv(find_dotenv())

smtp_server = os.getenv("SMTP_SERVER")
sender = os.getenv("EMAIL")
password = os.getenv("PASSWORD")


def convert_to_excel(transaction_content: List, transaction_type: str, start_date: str, end_date: str):
    file_name = f"{transaction_type}_{start_date}_{end_date}.xlsx"
    dir = Path.cwd() / "transaction"

    logger.info("making sure the dir exists...")
    dir.mkdir(parents=True, exist_ok=True)
    logger.info("done.")

    full_path = dir / file_name

    logger.info(f"writing the excel content to: {full_path}")
    try:
        df = pd.DataFrame(transaction_content)
        df["DATE"] = pd.to_datetime(df["DATE"])
        df = df.sort_values(by="DATE", ascending=True)
        df.to_excel(full_path, index=False)

    except Exception as e:
        logger.info(f"failed to write excel content to the file: {str(full_path)}")
        return f"{e}"


def send_email(email: str, transaction_type: str, start_date: str, end_date: str) -> None:
    msg = MIMEMultipart()
    msg["Subject"] = "An Automated Email from Python"
    msg["From"] = sender
    msg["To"] = email

    msg.attach(
        MIMEText(
            f"This email contains a transaction history of {transaction_type} from {start_date} to {end_date}",
            "plain",
        )
    )

    logger.info(f"sending email to: {email}...")
    file_name = f"{transaction_type}_{start_date}_{end_date}.xlsx"
    dir = Path.cwd() / "transaction"
    file_path = dir / file_name

    logger.info("attaching file to email...")
    with open(file_path, "rb") as file:
        attachment = MIMEApplication(file.read(), _subtype="xlsx")
        attachment.add_header("content-disposition", "attachment", filename=file_name)
        msg.attach(attachment)
        context = ssl.create_default_context()
    logger.info("done attaching file to email.")

    logger.info("sending email...")
    with smtplib.SMTP_SSL(smtp_server, port=465, context=context) as connection:
        connection.login(user=sender, password=password)
        connection.sendmail(from_addr=sender, to_addrs=email, msg=msg.as_string())
    logger.info(f"email successfully sent to: {sender}")
    logger.info(f"cleaning up dangling file at {str(file_path)}")
    shutil.rmtree(dir)
    logger.info("clean up done.")
