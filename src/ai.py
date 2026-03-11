from dotenv import load_dotenv, find_dotenv
from google import genai

load_dotenv(find_dotenv())

client = genai.Client()


def generate_transaction_sql(transaction_question: str) -> str:
    content = f"""
        Generate one sql query that i can pass to sqlalchemy. If the statement passed does not involve getting data
        from a database, return 'Invalid Prompt'. Also there are 2 main tables; DebitTransaction and CreditTransaction.
        Here are there columns;
            - debit_transactions: (id, amount (float), date_of_transaction, narration, is_savings, savings_account, receiver, airtime, phone_number, network, online_payment, service_for_online_payment, point_of_sale)
            - credit_transactions: (id, amount (float), date_of_transaction, narration, is_savings, savings_account, sender, reversal)
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
