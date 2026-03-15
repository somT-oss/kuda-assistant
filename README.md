## Kuda Assistant
This is a CLI tool that displays your kuda bank transactions in a clean and minimal look so you don't have to dig through your emails to look for transactions you've made in the past. 

This project was as a result of the frustration i faced when i noticed that after receiving money, i saw that i had spent it all without really knowing where my money was going. With this tool i can see exactly the transactions i've made, who i sent money too at any particular point in time and with the help of the inbuilt AI chat feature, I can get more detailed insights about my spendings.

## Features
There are 4 major feature provided by kuda assistant.
1. Initialize Database: ```ka init``` initializes the program to parse the first n transactions into the database so you can query it.
```bash
1. n flag. It's default is 10 and can be increased or decreased by passing the --n flag.

e.g
ka init. Parses the first 10 transactions.
ka init --n=100. Parses the first 100 transactions.
```
Note: *```ka init``` has a smart checkpoint in place to prevent parsing transactions that have already been parsed during prior calls.*


2. Retrieve Transactions: ```ka get``` with the get command, you can retrieve a list of your first n transactions. You can also filter the transactions by credit or debit transactions by passing the appropriate flags.
```bash
1. n flag. It's default is 10 and can be increased or decreased by passing the --n flag.

2. credit flag. When applied gets the first n credit transactions
3. debit flag. When applied gets the first n debit transactions

FORMAT: ka get start_date end_date --n=<number of transactions> email --credit | --debit

e.g
ka get 2026-01-01 2026-03-01. # This retrieves the first 10 debit and credit transactions.

ka get 2026-01-01 2026-03-01 --n=20. # This retrieves the first 20 debit and credit transactions.

ka get 2026-01-01 2026-03-01 --n=20 --credit. # This retrieves the first 20 credit transactions.

ka get 2026-01-01 2026-03-01 --n=20 --debit. # This retrieves the first 20 debit transactions.
```

3. Export Transactions: ```ka export``` with the export command, you can export your debit or credit transactions into excel files that will be sent directly to your email you provide like so.
```bash

defaults:
1. n parameter. It's default is 10 and can be increased or decreased by passing the --n flag.

FORMAT: ka export start_date end_date --n=<number of transactions> email --credit | --debit

e.g
ka export 2026-01-01 2026-03-01 youremail@gmail.com --credit. # This exports the first 10 credit transactions to your email as excel.

ka export 2026-01-01 2026-03-01 --n=20 youremail@gmail.com --credit. # This exports the first 20 credit transactions to your email as excel.

ka export 2026-01-01 2026-03-01 --n=50 youremail@gmail.com --debit. # This exports the first 50 debit transactions to your email as excel.
```

4. AI Chat: ```ka chat``` opens a REPL that takes in english queries, processes it returns the result from the database with the assistance of Google Gemini.

### Technologies Used
1. Python.
2. Postgres.
3. Redis.
4. Docker.
5. Makefile.

### Installation
You need to have the following prerequisites before installing the application.
- Python3.10+
- Docker.
- make.

1. Copy the environment variables from .env.example into your .env file.
```bash
cp .env.example .env
```

2. Fill in those environment variables with the appropriate values except for ```DATABASE_URL``` and ```REDIS_URL```, they will be injected from the ```docker-compose.yml``` files.

3. For ```EMAIL``` and ```PASSWORD```, you will need to provide the email and password that received Kuda email transaction receipts. You can create an **[App Password](https://myaccount.google.com/apppasswords)** for your email, this will serve as the email password

4. For ```SENDER_EMAIL``` and ```SENDER_PASSWORD``` use a separate email and create an app password too. If you do not have a second email, passing the values from ```EMAIL``` and ```PASSWORD``` will suffice. **This will mean you are sending an email to yourself**.

5. Run ```make build``` to build the tool and finally run ```make ka``` to add an alias ```ka``` to your ```.bashrc``` file so that you don't need to pass in the whole python command to run this tool. 

6. Run ```ka init``` to initialize the database with the first n transactions.

## Testing
I have written unittests to test key components of the tool. These tests are located in the *```test/```* folder. 
To run all tests in that folder run:
```bash
python -m unittest discover -s tests
```

## Screenshots