import zmq
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from prettytable import PrettyTable


load_dotenv()

uri = os.getenv("MONGODB_URI")
if uri is None:
    raise ValueError("MONGODB_URI is not valid.")

client = MongoClient(uri, server_api=ServerApi('1'))

def get_db():
    return client["budgetwise_db"]

def calculate_total_savings():
    db = get_db()
    source_collection = db.transactions
    savings_docs = list(source_collection.find({"type": "savings"}))

    table = PrettyTable()
    table.field_names = ["Date", "Amount (USD)"]
    table.align["Date"] = "l"
    table.align["Amount (USD)"] = "r"

    total = 0
    for doc in savings_docs:
        amount = doc.get("amount", 0)
        date = doc.get("date")

        table.add_row([date, f"${amount:,.2f}"])
        total += amount

        # Save to per-entry collection
        collection_name = "savings_transactions"
        savings_data = {"date": date, "amount": amount}
        if not db[collection_name].find_one(savings_data):
            db[collection_name].insert_one(savings_data)

    output = f"Savings Breakdown:\n{table}\nTotal Savings: ${total:,.2f}"
    return output

def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5552")

    print("Savings microservice running on tcp://*:5552")

    while True:
        message = socket.recv_string()
        print(f"Received request: {message}")

        if message == "get_total_savings":
            report = calculate_total_savings()
            socket.send_string(report)
        else:
            socket.send_string("Unknown command")

if __name__ == "__main__":
    try:
        # Test MongoDB connection on start
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        main()
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
