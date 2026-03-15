from sqlalchemy.exc import SQLAlchemyError
import typer
from sqlalchemy import select, literal_column, union_all
from src.ai import generate_transaction_sql
from src.logger import logger
from storage.base import Session
from storage.models import CreditTransaction, DebitTransaction
from sqlalchemy import text
from rich.console import Console
from rich.table import Table
from utils.utils import get_start_datetime_end_datetime
from utils.utils import convert_to_excel, send_email
from src.main import (
    create_tables,
    parse_and_load_transactions_to_db,
)


import logging

logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


app = typer.Typer(help="Kuda Assistant CLI - Simplified Transaction History in your Terminal")

@app.command()
def init(n: int = 50):
    """
    Initialize the database and parse the first n transactions from your email.
    """
    logger.info(f"parsing the first {n} transactions in your email.")
    create_tables()
    parse_and_load_transactions_to_db(n)
    logger.info("done parsing information your transactions into the db. you can query for your transactions now!")
    
@app.command()
def get(start_date: str, end_date: str, n: int = 10, credit: bool = False, debit: bool = False):
    """
    Get transactions from the database.
    """
    datetimes = get_start_datetime_end_datetime(start_date, end_date)
    if not datetimes:
        return None
    
    datetime_start_date, datetime_end_date = datetimes[0], datetimes[1]
    console = Console()
    
    if credit:
        with Session() as session:
            statement = (select(CreditTransaction)
                .where(
                    CreditTransaction.date_of_transaction >= datetime_start_date,
                    CreditTransaction.date_of_transaction <= datetime_end_date
                )
                .order_by(CreditTransaction.date_of_transaction.asc())
                .limit(n)
            )
            res = session.scalars(statement).all()
            if not res:
                console.print("[yellow]No credit transactions found in this date range.[/yellow]")
                return res
    
            table = Table(title="Credit Transactions", show_header=True, header_style="bold magenta")
            
            table.add_column("Date", style="cyan", justify="left")
            table.add_column("Amount", style="green", justify="right")
            table.add_column("Sender", style="white")
            table.add_column("Narration", style="dim", overflow="fold")
            table.add_column("From Savings", style="dim", overflow="fold")
            table.add_column("Savings Account", style="dim", overflow="fold")
            table.add_column("Reversal", style="dim", overflow="fold")
    
            for tx in res:
                date_str = tx.date_of_transaction.strftime("%Y-%m-%d")
                amount_str = f"₦{float(tx.amount)}0" 
                sender_str = tx.sender or "N/A"
                narration_str = tx.narration or "N/A"
                is_from_savings = "True" if tx.from_savings else "False"
                savings_account = tx.savings_account or "N/A"
                is_reversal = "True" if tx.reversal else "False"
                
                table.add_row(date_str, amount_str, sender_str, narration_str, is_from_savings, savings_account, is_reversal)
    
            console.print(table)
            print("\n")
            return res
    
    if debit:
        with Session() as session:
            statement = (select(DebitTransaction)
                .where(
                    DebitTransaction.date_of_transaction >= start_date,
                    DebitTransaction.date_of_transaction <= end_date
                )
                .order_by(DebitTransaction.date_of_transaction.asc())
                .limit(n)
            )
            res = session.scalars(statement).all()
            
            table = Table(title="Raw Debit Transactions", show_header=True, header_style="bold red")
                    
            table.add_column("Date", style="cyan")
            table.add_column("Amount", style="red", justify="right")
            table.add_column("Receiver", style="white", overflow="fold")
            table.add_column("Narration", style="dim", overflow="fold")
            table.add_column("Airtime", justify="center")
            table.add_column("Phone Number", style="white")
            table.add_column("Network", style="white")
            table.add_column("Online Payment", justify="center")
            table.add_column("Service (Online)", overflow="fold")
            table.add_column("POS", justify="center")
            table.add_column("Savings", justify="center")
    
            for tx in res:
                date_str = tx.date_of_transaction.strftime("%Y-%m-%d") if tx.date_of_transaction else "N/A"
                amount_str = f"{float(tx.amount)}0" if tx.amount else "0.00"
                narration_str = tx.narration or "N/A"
                
                receiver_str = tx.receiver or "N/A"
                phone_str = tx.phone_number or "N/A"
                network_str = tx.network or "N/A"
                service_str = tx.service_for_online_payment or "N/A"
                
                airtime_str = "True" if tx.airtime else "N/A"
                online_str = "True" if tx.online_payment else "N/A"
                pos_str = "True" if tx.point_of_sale else "N/A"
                savings_str = "True" if tx.savings else "N/A"
                
                table.add_row(
                    date_str, 
                    amount_str, 
                    receiver_str, 
                    narration_str,
                    airtime_str, 
                    phone_str, 
                    network_str, 
                    online_str, 
                    service_str, 
                    pos_str, 
                    savings_str
                )
    
            console.print(table)
            return res
    
    with Session() as session:
        s1 = select(
            CreditTransaction.id, 
            CreditTransaction.amount, 
            CreditTransaction.date_of_transaction,
            literal_column("'credit'").label("type")
        ).where(CreditTransaction.date_of_transaction.between(start_date, end_date))

        s2 = select(
            DebitTransaction.id, 
            DebitTransaction.amount, 
            DebitTransaction.date_of_transaction,
            literal_column("'debit'").label("type")
        ).where(DebitTransaction.date_of_transaction.between(start_date, end_date))

        statement = union_all(s1, s2).order_by(literal_column("date_of_transaction").asc()).limit(n)
        res = session.execute(statement).all()
        
        if not res:
            console.print("[yellow]No transactions found in this date range.[/yellow]")
            return res
    
        table = Table(title="Combined Bank Statement", show_header=True, header_style="bold blue")
        
        table.add_column("Date", style="cyan", justify="left")
        table.add_column("Type", justify="center")
        table.add_column("Amount", justify="right")
        table.add_column("Transaction ID", style="dim", overflow="fold")
    
        for row in res:
            date_str = row.date_of_transaction.strftime("%Y-%m-%d %H:%M") if row.date_of_transaction else "N/A"
            id_str = str(row.id)
        
            if row.type == 'credit':
                type_str = "[bold green]CREDIT[/bold green]"
                amount_str = f"[green]+₦{float(row.amount):,.2f}[/green]"
            else:
                type_str = "[bold red]DEBIT[/bold red]"
                amount_str = f"[red]-₦{float(row.amount):,.2f}[/red]"
                
            table.add_row(date_str, type_str, amount_str, id_str)
        console.print(table)
        return res
        
@app.command()
def export(start_date: str, end_date: str, email: str, credit: bool = False, debit: bool = False):
    """
    Export transactions to an Excel file and send it to your email.
    """
    if not credit and not debit:
        logger.error("you need to specify credit or debit transaction to export.")
        return
    
    datetimes = get_start_datetime_end_datetime(start_date, end_date)
    if not datetimes:
        return None
    
    datetime_start_date, datetime_end_date = datetimes[0], datetimes[1]
    trxn_list = []
    if credit:
        with Session() as session:
            statement = (select(CreditTransaction)
                .where(
                    CreditTransaction.date_of_transaction >= datetime_start_date,
                    CreditTransaction.date_of_transaction <= datetime_end_date
                )
                .order_by(CreditTransaction.date_of_transaction.asc())
            )
            res = session.scalars(statement).all()
            
            # convert res to a list of dictionary transactions
            for trxn in res:
                trxn_dict = {}
                trxn_dict['date'.upper()] = trxn.date_of_transaction.strftime("%Y-%m-%d")
                trxn_dict['amount'.upper()] = f"₦{float(trxn.amount)}0" 
                trxn_dict['sender'.upper()] = trxn.sender or "N/A"
                trxn_dict['narration'.upper()] = trxn.narration or "N/A"
                trxn_dict['is_from_savings'.upper()] = "True" if trxn.from_savings else "False"
                trxn_dict['savings_account'.upper()] = trxn.savings_account or "N/A"
                trxn_dict['is_reversal'.upper()] = "True" if trxn.reversal else "False"
                
        
                trxn_list.append(trxn_dict)

        convert_to_excel(trxn_list, "credit", start_date, end_date)
        send_email(email, "credit", start_date, end_date)
        convert_to_excel.delay(trxn_list, "credit", start_date, end_date)
        send_email.delay(email, "credit", start_date, end_date)
        return "Your transaction excel sheet is currently being processed and will be sent to you shortly!"
     
        
    if debit:
        with Session() as session:
            statement = (select(DebitTransaction)
                .where(
                    DebitTransaction.date_of_transaction >= start_date,
                    DebitTransaction.date_of_transaction <= end_date
                )
                .order_by(DebitTransaction.date_of_transaction.asc())
            )
            res = session.scalars(statement).all()
            trxn_list = []
            for trxn in res:
                trxn_dict = {}
                trxn_dict['date'.upper()] = trxn.date_of_transaction.strftime("%Y-%m-%d")
                trxn_dict['amount'.upper()] = f"{float(trxn.amount)}0" if trxn.amount else "0.00"
                trxn_dict['narration'.upper()] = trxn.narration or "N/A"
                trxn_dict['receiver'.upper()] = trxn.receiver or "N/A"
                trxn_dict['phone'.upper()] = trxn.phone_number or "N/A"
                trxn_dict['network'.upper()] = trxn.network or "N/A"
                trxn_dict['service'.upper()] = trxn.service_for_online_payment or "N/A"
                trxn_dict['airtime'.upper()] = "True" if trxn.airtime else "N/A"
                trxn_dict['online'.upper()] = "True" if trxn.online_payment else "N/A"
                trxn_dict['pos'.upper()] = "True" if trxn.point_of_sale else "N/A"
                trxn_dict['savings'.upper()] = "True" if trxn.savings else "N/A"
                
                trxn_list.append(trxn_dict)
            convert_to_excel(trxn_list, "debit", start_date, end_date)
            send_email(email, "debit", start_date, end_date)
            
@app.command()
def chat():
    """
    Chat with the AI assistant to get insights about your transactions.
    """
    while True:
        question = input(">>> ")
        query = generate_transaction_sql(question) 
        console = Console()
        
        with Session() as session:
            try:
                result = session.execute(text(query))
                
                rows = result.fetchall()
                
                if not rows:
                    console.print("[yellow]The query ran successfully, but returned 0 results.[/yellow]")
                    return
                column_names = result.keys()
                table = Table(title="AI Insight Results", show_header=True, header_style="bold magenta")
                for col in column_names:
                    clean_name = str(col).replace("_", " ").title()
                    table.add_column(clean_name, style="cyan")
                for row in rows:
                    row_data = [str(item) if item is not None else "-" for item in row]
                    table.add_row(*row_data)
                console.print(table)
                print()
    
            except SQLAlchemyError as e:
                console.print("[bold red]Database Error: The AI generated invalid SQL.[/bold red]")
                console.print(f"[red]{e}[/red]")

        
if __name__ == "__main__":
    app()