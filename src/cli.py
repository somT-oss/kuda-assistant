import typer
from sqlalchemy import select, literal_column, union_all
from storage.base import Session
from storage.models import CreditTransaction, DebitTransaction
from src.logger import logger
from datetime import datetime
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Kuda Assistant CLI - Simplified Transaction History in your Terminal")

@app.command()
def get(start_date: str, end_date: str, n: int = 10, credit: bool = False, debit: bool = False):
    datetime_start_date: datetime
    datetime_end_date: datetime
    
    # check date format.
    try:
        datetime_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        datetime_end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        logger.info(f"Could not convert {start_date} or {end_date} to datetime obj. Incorrect format for {start_date} or {end_date}")
        return 
    
    console = Console()
    
    # check if start_date > end_date
    if datetime_start_date > datetime_end_date:
        logger.info(f"start_date: {start_date} cannot be greater than end_date: {end_date}")
        return 
    
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
def recent():
   pass
   
@app.command()
def chat():
    pass
    
if __name__ == "__main__":
    app()