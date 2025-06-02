import zmq
import matplotlib.pyplot as plt
import io
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["budgetwise_db"]
transactions = db["transactions"]

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5554")

print("Microservice running on port 5554...")

while True:
    print("Waiting for request...")
    message = socket.recv_string()
    print("Received:", message)

    if message != "generate_chart":
        socket.send_string("Invalid request")
        continue

    pipeline = [{"$group": {"_id": "$type", "total": {"$sum": "$amount"}}}]
    results = list(transactions.aggregate(pipeline))
    print("Aggregation results:", results)

    if not results:
        socket.send_string("No data found to generate chart.")
        continue

    try:
        # Build chart in memory
        types = [r["_id"] for r in results]
        totals = [abs(r["total"]) for r in results]

        plt.figure(figsize=(6, 4))
        plt.bar(types, totals, color=["green" if t == "income" else "red" for t in types])
        plt.title("Income vs Expense")
        plt.ylabel("Amount")
        plt.xlabel("Type")

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)

        socket.send(buf.read())  # Send binary image data directly
        print("Chart sent to client.")
    except Exception as e:
        print("Error:", e)
        socket.send_string(f"Error: {e}")
