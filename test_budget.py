#!/usr/bin/env python3
"""
test_budget.py

Interactive CLI that:
1) Connects directly to MongoDB to show all transactions.
2) Prompts user to filter by month, type, or ID.
3) Sends JSON to the microservice over ZeroMQ.
4) Displays the filtered results in a clean table format.
5) Continues on Enter; exits on any other key.
"""
import os
import time
import zmq
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
from tabulate import tabulate

# --- Setup ---
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI not set in .env")

# MongoDB client
tx_client = MongoClient(
    MONGO_URI,
    server_api=ServerApi("1"),
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000
)
db = tx_client["budgetwise_db"]
transactions = db.transactions

MICRO_URL = "tcp://localhost:5555"

# Utility functions
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_all_transactions():
    rows = []
    for txn in transactions.find():
        rows.append([
            str(txn["_id"]),
            txn.get("date", ""),
            txn.get("type", ""),
            txn.get("description", ""),
            txn.get("category", ""),
            f"${txn.get('amount', 0):.2f}"
        ])
    print(tabulate(rows,
                   headers=["ID", "Date", "Type", "Description", "Category", "Amount"],
                   tablefmt="fancy_grid"))

# Display microservice response
def display_response(resp):
    if isinstance(resp, dict) and resp.get("error"):
        print(f"Error: {resp['error']}")
    else:
        docs = resp if isinstance(resp, list) else [resp]
        rows, headers = [], ["ID", "Date", "Type", "Description", "Category", "Amount"]
        for d in docs:
            rows.append([
                d.get("_id", ""),
                d.get("date", ""),
                d.get("type", ""),
                d.get("description", ""),
                d.get("category", ""),
                f"${d.get('amount', 0):.2f}"
            ])
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

# Call microservice and display clean table
def call_microservice(req):
    ctx  = zmq.Context()
    sock = ctx.socket(zmq.REQ)
    sock.connect(MICRO_URL)
    print(f"\nSending: {req}")
    sock.send_json(req)
    resp = sock.recv_json()
    print("Filtered Results:")
    display_response(resp)

# Main interactive loop
def main():
    while True:
        clear_screen()
        print("=== All Transactions ===\n")
        show_all_transactions()
        print("\n--- Filter Transactions ---\n")
        print("1) Filter by Month (YYYY-MM)")
        print("2) Filter by Type (income/expense)")
        print("3) Filter by Transaction ID")
        print("4) Exit")
        choice = input("Choose an option [1-4]: ").strip()

        if choice == '4':
            print("Goodbye!")
            break
        if choice == '1':
            month = input("Enter month (YYYY-MM): ").strip()
            req = {"month": month}
        elif choice == '2':
            tx_type = input("Enter type (income/expense): ").strip().lower()
            req = {"type": tx_type}
        elif choice == '3':
            txn_id = input("Enter Transaction ID: ").strip()
            req = {"id": txn_id}
        else:
            print("Invalid choice.")
            time.sleep(1)
            continue

        call_microservice(req)
        again = input("\nPress Enter to filter again; any other button to exit ")
        if again != "":
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()
