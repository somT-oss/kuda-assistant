import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import String
from sqlalchemy import func
from datetime import datetime
from storage.base import Base

class Transaction(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    transfer: Mapped[bool | None]
    narration: Mapped[str | None] = mapped_column(String(250))
    date_of_transaction: Mapped[datetime]
    amount: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] =  mapped_column(default=func.now())

class CreditTransaction(Transaction):
    __tablename__ = "credit_transactions"

    sender: Mapped[str | None] = mapped_column(String(100))
    reversal: Mapped[bool | None]
    from_savings: Mapped[bool | None]
    savings_account: Mapped[str | None]
    
    def __repr__(self) -> str:
        return f"Transaction type: Credit. id: {self.id}"

class DebitTransaction(Transaction):
    __tablename__ = "debit_transactions"
    
    receiver: Mapped[str | None] = mapped_column(String(100))
    airtime: Mapped[bool | None]
    phone_number: Mapped[str | None] = mapped_column(String(11))
    network: Mapped[str | None] = mapped_column(String(10))
    online_payment: Mapped[bool | None]
    service_for_online_payment: Mapped[str | None] = mapped_column(String(150))
    point_of_sale: Mapped[bool | None]
    savings: Mapped[bool | None]
    # savings_account: Mapped[str | None]
    
    def __repr__(self) -> str:
        return f"Transaction type: Debit. id: {self.id}"
    
    
    
    
    
