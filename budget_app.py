from db_connection import get_db
from bson.objectid import ObjectId
import os
from tabulate import tabulate
import time
import csv


# Displays title of application in ASCII Artstyle 
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
# Clears the console screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
# Displays the mainn menu and choices
def main_menu():
    """
    Displays the main menu and prompts the user for a choice.
    Returns the user's choice as an integer.
    """
    print("Welcome to BudgetWise your personal budget app!\n")
    print("Take control of your finances!")
    print("Record your transactions, view your budget, and set goals.\n")
    print("Please select an option:")
    print("1. Manage your transactions")
    print("2. View your budget")
    print("3. Create your budget goals")    
    print("4. Exit")

# Displays the transaction management menu
def transaction_management_menu():
    """
    Displays the transaction management menu and prompts the user for a choice.
    Returns the user's choice as an integer.
    """
    print("\n---Transaction Management Menu---")
    print("1. Add a transaction")
    print("2. Delete a transaction")
    print("3. Edit transactions")
    print("4. Export transactions")
    print("5. Back to main menu")

# Displays the budget goals menu
def budget_goals_menu():
    """
    Displays the budget goals menu and prompts the user for a choice.
    """
    print("---Budget Goals Menu---")
    print("1. Create a new budget goal")
    print("2. Update a budget goal")
    print("3. Delete a budget goal")
    print("4. Back to main menu")

# adds transactions to the database
def add_transaction():
    """
    Function to add a transaction to MongoDB.
    """
    db = get_db()
    transactions = db.transactions

    date = input("Enter the date (YYYY-MM-DD): ").strip()
    type = input("Enter the type (Income/Expense/Custom Type): ").strip().lower()
    description = input("Enter a description: ").strip().lower()
    category = input("Enter a category (Food, Rent, etc.): ").strip().lower()
    amount = float(input("Enter the amount (use negative for expenses): $"))

    transaction = {
        "date": date,
        "type": type,
        "description": description,
        "category": category,
        "amount": amount
    }

    result = transactions.insert_one(transaction)
    print(f"Transaction saved with ID: {result.inserted_id}\n")

# edits transactions in the database
def edit_transactions():
    """
    Function that lets a user edit their transactions in MongoDB, allows editing multiple times until the user exits.
    """
    db = get_db()
    transactions = db.transactions

    while True:
        clear_screen()
        view_transactions()

        transaction_id = input("\nEnter the transaction ID to edit (or type 'cancel' to return to the menu): ").strip()
        if transaction_id.lower() == 'cancel':
            print("Update cancelling...")
            time.sleep(2)
            clear_screen()
            break

        if not ObjectId.is_valid(transaction_id):
            print("Invalid transaction ID. Please try again.\nPage will auto refresh in 5 seconds.")
            time.sleep(5)
            continue

        transaction = transactions.find_one({"_id": ObjectId(transaction_id)})

        if transaction:
            print("\n--- Current Transaction ---")
            print(f"Date       : {transaction['date']}")
            print(f"Type       : {transaction['type']}")
            print(f"Description: {transaction['description']}")
            print(f"Category   : {transaction['category']}")
            print(f"Amount     : ${transaction['amount']:.2f}")

            update_date = input("Enter new date (leave blank for no change): ").strip()
            update_type = input("Enter new type (leave blank for no change): ").strip().lower()
            update_description = input("Enter new description (leave blank for no change): ").strip().lower()
            update_category = input("Enter new category (leave blank for no change): ").strip().lower()
            update_amount = input("Enter new amount (leave blank for no change): ").strip()

            update_fields = {}
            if update_date:
                update_fields['date'] = update_date
            if update_type:
                update_fields['type'] = update_type
            if update_description:
                update_fields['description'] = update_description
            if update_category:
                update_fields['category'] = update_category
            if update_amount:
                update_fields['amount'] = float(update_amount)

            if update_fields:
                transactions.update_one({"_id": ObjectId(transaction_id)}, {"$set": update_fields})
                print("Your transaction were updated.\n")
            else:
                print("No changes were made.\n")

# deletes transactions in the database
def delete_transaction():
    """
    Function to delete a transaction.
    """
    db = get_db()
    transactions = db.transactions

    while True:
        clear_screen()
        view_transactions()
        transaction_id = input("Enter the transaction ID to delete (or type 'cancel' to go back): ").strip()

        if transaction_id.lower() == 'cancel':
            print("Cancelling deletion...")
            time.sleep(2)
            clear_screen()
            break

        for transaction in transactions.find():
            if str(transaction['_id']) == transaction_id:
                confirm = input("Are you sure you want to delete this transaction? (Doing so will permanently delete it.) (y/n): ").strip().lower()
                if confirm == 'y':
                    transactions.delete_one({'_id': transaction['_id']})
                    print("Transaction successfully deleted.")
                    time.sleep(2)
                    clear_screen()
                    return
                else:
                    print("Deletion cancelled.")
                    time.sleep(2)
                    clear_screen()
                    return

        print("Transaction ID not found. Please try again. Page will auto refresh in 5 seconds.")
        time.sleep(5)

# display transactions in a table format
def view_transactions():
    db = get_db()
    transactions = db.transactions.find()

    table = []
    headers = ["Transaction ID", "Date", "Type", "Description", "Category", "Amount"]

    for transaction in transactions:
        row = [
            str(transaction["_id"]),
            transaction["date"],
            transaction["type"],
            transaction["description"],
            transaction["category"],
            f"${transaction['amount']:.2f}"
        ]
        table.append(row)

    print("\n--- Transactions ---")
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

# Displays a brief budget overview
def view_budget():
    """
    Function to view the budget.
    """
    db = get_db()
    transactions = db.transactions.find()
    income = 0
    expenses = 0
    for transaction in transactions:
        amount = transaction['amount']
        if amount >= 0:
            income += amount
        else:
            expenses += amount
    print(f"\nTotal Income: ${income:.2f}")
    print(f"Total Expenses: ${expenses:.2f}")
    print(f"Net Spending: ${income + expenses:.2f}")

# Creates a budget goal in the database
def create_budget_goal():
    """
    Function to create a budget goal.
    """
    db = get_db()
    budget_goals = db.budget_goals
    clear_screen()
    goal_name = input("Enter the name of the budget goal: ").strip()
    target_amount = float(input("Enter the target amount: $"))
    current_amount = float(input("Enter the current amount: $"))

    budget_goal = {
        "goal_name": goal_name,
        "target_amount": target_amount,
        "current_amount": current_amount
    }

    budget_goals.insert_one(budget_goal)

# Displays the budget goals in a table format
def view_budget_goals():
    """
    Function to view budget goals.
    """
    db = get_db()
    budget_goals = db.budget_goals.find()
    print("\n--- Budget Goals ---")
    table = []
    headers = ["Goal ID", "Goal", "Target Amount", "Current Amount"]

    for goal in budget_goals:
        row = [
            str(goal["_id"]),
            goal["goal_name"],
            f"${goal['target_amount']:.2f}",
            f"${goal['current_amount']:.2f}",

        ]
        table.append(row)
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

# Updates a budget goal in the database
def update_budget_goal():
    """
    Function to update a budget goal.
    """
    db = get_db()
    budget_goals = db.budget_goals

    while True:
        clear_screen()
        view_budget_goals()

        goal_id = input("Enter the ID of the budget goal to update (or type 'cancel' to go back): ").strip()

        if goal_id.lower() == "cancel":
            print("Update cancelling...")
            time.sleep(2)
            break

        if not ObjectId.is_valid(goal_id):
            print("Invalid budget goal ID. Please try again.\nPage will auto refresh in 5 seconds.")
            time.sleep(5)
            continue

        budget_goal = budget_goals.find_one({"_id": ObjectId(goal_id)})

        if budget_goal:
            print(f"\nCurrent budget goal: {budget_goal}")
            print(f"Goal          : {budget_goal['goal_name']}")
            print(f"Target Amount : ${budget_goal['target_amount']}")
            print(f"Current Amount: ${budget_goal['current_amount']}\n")

            update_goal_name = input("Enter new goal name (leave blank if for no change): ").strip()
            update_target_amount = input("Enter new target amount (leave blank for no change): $").strip()
            update_current_amount = input("Enter new current amount (leave blank for no change): $").strip()

            update_fields = {}
            if update_goal_name:
                update_fields['goal_name'] = update_goal_name
            if update_target_amount:
                update_fields['target_amount'] = float(update_target_amount)
            if update_current_amount:
                update_fields['current_amount'] = float(update_current_amount)

            if update_fields:
                budget_goals.update_one({"_id": ObjectId(goal_id)}, {"$set": update_fields})
                print("Your budget goal was successfully updated.")
            else:
                print("No changes were made to your Goals.")

# Deletes a budget goal in the database
def delete_budget_goal():
    """
    Function to delete a budget goal in mongodb.
    """
    db = get_db()
    budget_goals = db.budget_goals

    while True:
        clear_screen()
        view_budget_goals()
        goal_id = input("Enter the budget goal ID to delete (or type 'cancel' to go back): ").strip().lower()

        if goal_id == 'cancel':
            print("Cancelling deletion...")
            time.sleep(2)
            break

        for goal in budget_goals.find():
            if str(goal['_id']) == goal_id:
                confirm = input("Are you sure you want to delete this goal? (Doing so will delete all progress.) (y/n): ").strip().lower()
                if confirm == 'y':
                    print("Budget goal successfully deleted.")
                    time.sleep(2)
                    budget_goals.delete_one({'_id': goal['_id']})
                    return
                else:
                    print("Deletion cancelled.")
                    time.sleep(2)
                    break
        
        print("Budget goal ID not found. Please try again. Page is refreshing...")
        time.sleep(2)

def export_transactions():
    """
    Function to export transactions to a CSV file.
    """
    db = get_db()
    transactions = db.transactions.find()

    with open('transactions.csv', 'w', newline='') as csvfile:
        headers = ['Transaction ID', 'Date', 'Type', 'Description', 'Category', 'Amount']
        writer = csv.DictWriter(csvfile, fieldnames=headers)

        writer.writeheader()
        for transaction in transactions:
            writer.writerow({
                'Transaction ID': str(transaction['_id']),
                'Date': transaction['date'],
                'Type': transaction['type'],
                'Description': transaction['description'],
                'Category': transaction['category'],
                'Amount': transaction['amount']
            })

    print("Transactions were exported to transactions.csv.")
    print("Returning to Transaction Management Menu...")
    time.sleep(3)

# This is the main program loop that will run until the user chooses to exit.
while True:
    clear_screen()
    choice = 0
    title()
    main_menu()
    choice = input("\nEnter a number between 1 and 4: ")

    if choice == '1':
        while True:
            clear_screen()
            view_transactions()
            transaction_management_menu()

            choice = input("Enter a number between 1 and 4: ")
            if choice == '1':
                print("--Add Transaction--")
                add_transaction()
            elif choice == '2':
                print("--Delete Transaction--")
                delete_transaction()
            elif choice == '3':
                print("--Edit Transactions--")
                edit_transactions()
            elif choice == '4':
                export_transactions()
            elif choice == '5':
                break
            else:
                print("Invalid choice, choose a number between 1-4.")
    elif choice == '2':
        clear_screen()
        print("---Budget Overview---")
        while True:
            choice = input("Do you want to view your transactions or go back to the main menu (y/n/exit)? ").lower()
            if choice == 'y':
                view_transactions()
                view_budget()
            elif choice == 'n':
                view_budget()

            elif choice == 'exit':
                break
            else:
                print("Invalid choice, please type 'y', 'n', or 'exit'.")
        view_budget()
    elif choice == '3':
        while True:
            clear_screen()
            view_budget_goals()
            budget_goals_menu()
            choice = input("Enter a number between 1 and 4: ")
            if choice == '1':
                print("--Create a new budget goal--")
                create_budget_goal()
            elif choice == '2':
                print("--Update a budget goal--")
                update_budget_goal()
            elif choice == '3':
                print("--Delete a budget goal--")
                delete_budget_goal()
            elif choice == '4':
                break
            else:
                print("Invalid choice, choose a number between 1-5.")
        print("Budget Goals")
    elif choice == '4':
        print("Exiting, goodbye!")
        time.sleep(2)
        clear_screen()
        break
    else:
        print("Invalid choice, please select a number between 1-4.")
        time.sleep(2)
