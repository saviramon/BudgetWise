import zmq
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB URI from .env
uri = os.getenv("MONGODB_URI")
if not uri:
    raise ValueError("MONGODB_URI is not set in .env")

# Connect to MongoDB 
client = MongoClient(uri)

try:
    client.admin.command("ping")
    print("Connected to MongoDB")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)

# Database and collections
recurring_db = client["RecurringTransactions"]
recurring_col = recurring_db["recurringTransactions"]
budget_db = client["budgetwise_db"]
transactions_col = budget_db["transactions"]

# ZeroMQ REP socket setup
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5557")

# Frequency to days mapping
FREQUENCY_TO_DAYS = {
    "daily": 1,
    "bi-weekly": 14,
    "monthly": 30 
}

def apply_recurring_transactions():
    today = datetime.today().date()
    print(f"Applying recurring transactions for {today}")
    processed = []

    for doc in recurring_col.find():
        print(f"Checking doc: {doc}")

        freq = doc.get("recurrence", {}).get("frequency")
        next_due_str = doc.get("recurrence", {}).get("next_due")

        print(f"Frequency: {freq}, Next Due: {next_due_str}")

        if not freq or not next_due_str:
            print("missing frequency or next_due")
            continue

        try:
            next_due = datetime.strptime(next_due_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"invalid date format for next_due: {next_due_str}")
            continue

        print(f"Today: {today}, Next Due: {next_due}")

        if today >= next_due:
            print("Processing transaction")

            amount = doc.get("amount", 0)
            txn_type = doc.get("type")
            if not txn_type:
                txn_type = "income" if amount > 0 else "expense"

            # Makes sure expense is negative and income is positive
            if txn_type == "expense" and amount > 0:
                amount = -abs(amount)
            elif txn_type == "income" and amount < 0:
                amount = abs(amount)

            transaction = {
                "date": str(today),
                "type": txn_type,
                "description": doc.get("description", "no description"),
                "category": doc.get("category", "uncategorized"),
                "amount": amount
            }

            try:
                insert_result = transactions_col.insert_one(transaction)
                print(f"Inserted transaction with id {insert_result.inserted_id}")
            except Exception as e:
                print(f"Failed to insert transaction: {e}")
                continue

            # Updates the next_due date based on frequency
            delta_days = FREQUENCY_TO_DAYS.get(freq, 30)
            new_due_date = next_due + timedelta(days=delta_days)
            try:
                update_result = recurring_col.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"recurrence.next_due": str(new_due_date)}}
                )
                print(f"Updated recurring transaction: {update_result.matched_count}, modified: {update_result.modified_count}")
            except Exception as e:
                print(f"Failed to update recurring transaction: {e}")

            processed.append(transaction)
        else:
            print("Not due yet")

    return processed


print("Microservice B Running on port 5557")
while True:
    try:
        message = socket.recv_json()
        command = message.get("command")

        if command == "add_recurring":
            try:
                transaction = message["transaction"]
                recurring_col.insert_one(transaction)
                processed = apply_recurring_transactions()
                socket.send_json({
                    "status": "Recurring transaction added",
                    "Transaction(s) added": len(processed)
                })
            except Exception as e:
                socket.send_json({"status": "error", "message": str(e)})

        elif command == "apply_recurring":
            try:
                processed = apply_recurring_transactions()
                socket.send_json({
                    "status": "Recurring transaction added",
                    "processed_count": len(processed)
                })
            except Exception as e:
                socket.send_json({"status": "error", "message": str(e)})

        else:
            socket.send_json({"status": "error", "message": "Unknown command"})
    except Exception as e:
        socket.send_json({"status": "error", "message": f"Server error: {str(e)}"})
