import os
import csv
from db_connection import get_db
from datetime import datetime

# Text to ASCII Art Generator (https://patorjk.com/software/taag/#p=display&h=1&v=0&f=Slant&t=BudgetWise)
def title():
    """
    Displays the title of the application.
    """
    print(r"""__________          .___              __   __      __.__               
\______   \__ __  __| _/ ____   _____/  |_/  \    /  \__| ______ ____  
 |    |  _/  |  \/ __ | / ___\_/ __ \   __\   \/\/   /  |/  ___// __ \ 
 |    |   \  |  / /_/ |/ /_/  >  ___/|  |  \        /|  |\___ \\  ___/ 
 |______  /____/\____ |\___  / \___  >__|   \__/\  / |__/____  >\___  >
        \/           \/_____/      \/            \/          \/     \/ """)
    
def main_menu():
    """
    Displays the main menu and prompts the user for a choice.
    Returns the user's choice as an integer.
    """
    print("Welcome to BudgetWise your personal budget app!\n")
    print("Please select an option:")
    print("1. Manage your transactions")
    print("2. View your budget")
    print("3. Create your budget goals")    
    print("4. Exit")
def transaction_management():
    """
    Displays the transaction management menu and prompts the user for a choice.
    Returns the user's choice as an integer.
    """
    print("\n---Transaction Management Menu---")
    print("1. Add a transaction")
    print("2. Delete a transaction")
    print("3. View transactions")
    print("4. Back to main menu")

def add_transaction():
    """
    Function to add a transaction to MongoDB.
    """
    db = get_db()
    transactions = db.transactions  # You can name your collection "transactions"

    date_str = input("Enter the date (YYYY-MM-DD): ").strip()
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format.")
        return

    tx_type = input("Enter the type (e.g., Income, Expense): ").strip()
    description = input("Enter a description: ").strip()
    category = input("Enter a category (e.g., Food, Rent, etc.): ").strip()

    try:
        amount = float(input("Enter the amount (use negative for expenses): "))
    except ValueError:
        print("Invalid amount.")
        return

    transaction = {
        "date": date,
        "type": tx_type,
        "description": description,
        "category": category,
        "amount": amount
    }

    result = transactions.insert_one(transaction)
    print(f"Transaction saved with ID: {result.inserted_id}\n")


def delete_transaction():
    """
    Function to delete a transaction."""
    pass

def view_transactions_mongo():
    """
    Function to view transactions in MongoDB.
    """
    db = get_db()
    transactions = db.transactions.find()

    print("\n--- View Transactions ---")
    for tx in transactions:
        print(f"{tx['date']} | {tx['type']} | {tx['description']} | {tx['category']} | ${tx['amount']:.2f}")

def view_budget():
    """
    Function to view the budget."""
    pass

while True:
    choice = 0
    title()
    main_menu()
    choice = input("\nEnter a number between 1 and 4: ")

    if choice == '1':
        while True:
            transaction_management()
            choice = input("Enter a number between 1 and 4: ")
            if choice == '1':
                print("--Add Transaction--")
                add_transaction()
            elif choice == '2':
                print("--Delete Transaction--")
                delete_transaction()
            elif choice == '3':
                print("--View Transactions--")
                view_transactions_mongo()
            elif choice == '4':
                break
            else:
                print("Invalid choice, choose a number between 1-4.")

    elif choice == '2':
        print("---Budget Overview---")
        view_budget()
    elif choice == '3':
        print("Budget Goals")

    elif choice == '4':
        print("Exiting, goodbye!")
        break
    else:
        print("Invalid choice, please select a number between 1-4.")

    

