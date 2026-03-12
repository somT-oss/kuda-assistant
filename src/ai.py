from dotenv import load_dotenv, find_dotenv
from google import genai

load_dotenv(find_dotenv())

client = genai.Client()


def generate_transaction_sql(transaction_question: str) -> str:
    content = f"""
        Generate one sql query that i can pass to sqlalchemy. If the statement passed does not involve getting data
        from a database, return 'Invalid Prompt'. Also there are 2 main tables; DebitTransaction and CreditTransaction.

        CRITICAL RULES: 
            1. You must query the physical database tables, NOT the Python classes. 
               Tables: debit_transactions, credit_transactions
            2. For boolean columns (like airtime, online_payment, is_savings), NEVER use 1 or 0. You MUST use TRUE or FALSE (e.g., WHERE airtime = TRUE).
            3. For date math, NEVER use SQLite syntax like date('now', '-x days'). You MUST use standard PostgreSQL interval math (e.g., CURRENT_DATE - INTERVAL '12 days').
            
        Here are there columns;
            - debit_transactions: (id, amount (float), date_of_transaction(string), narration, is_savings, savings_account, receiver, airtime, phone_number, network, online_payment, service_for_online_payment, point_of_sale)
            - credit_transactions: (id, amount (float), date_of_transaction(string), narration, is_savings, savings_account, sender, reversal)
        Make sure the resulting query generates a query using either of those tables.
        
        question: {transaction_question} 
    """
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=content
        )

        result = response.text.strip()
        if result.startswith("```sql"):
            result = result.replace("```sql", "").replace("```", "").strip()
        return result

    except Exception as e:
        print(f"the error: {e} occurred")
        return "invalid query"
