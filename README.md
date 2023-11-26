# Kuda Assistant

## Overview

Kuda Assistant is a Python-based bot designed to streamline the process of organizing and classifying transaction receipts from your Kuda bank account. The bot scrapes your email for Kuda transaction receipts, classifies each transaction into debit and credit, generates an Excel file with the results, and then sends it to your specified email address. By default, the bot gathers transaction receipts from the last two weeks.

## Debit and Credit Classification Methods

The bot implements various methods to distinguish between debit and credit transactions. The following methods have been implemented:

### Debit Methods

- **Airtime:** Transactions related to purchasing airtime.
- **Spend and Save:** Transactions related to spending or saving money.
- **Card Usage:** Transactions involving the use of the card online, at Point of Sale (POS), or at an ATM.
- **Transfer:** Transactions involving money transfers.

### Credit Methods

- **Transfer:** Credit transactions related to receiving money through transfers.
- **Transfer Reversal:** Credit transactions resulting from reversed transfers.

## Environmental Variables

To use the Kuda Assistant, you need to set up the following environmental variables:

1. Create a `.env` file in the root directory of the project.

2. Add the following variables to your `.env` file:

    ```env
    RECEIVER_EMAIL=your_receiver_email@gmail.com
    RECEIVER_PASSWORD=your_receiver_password
    SENDER_EMAIL=your_sender_email@gmail.com
    SENDER_PASSWORD=your_sender_password
    MONGODB_USERNAME=your_mongodb_username
    MONGODB_PASSWORD=your_mongodb_password
    ```

## Technologies Used

- **Python:** The primary programming language used for the development of the bot.
- **MongoDB:** The database used to store data.

## Setup

1. Install the required dependencies by running:

   ```bash
   pip install -r requirements.txt
