#!/usr/bin/env python3
"""
Microservice A: Transaction Filtering 

Listens on ZeroMQ REP at tcp://0.0.0.0:5555.
Accepts JSON requests to:
  - Filter by month ("YYYY-MM")
  - Filter by type ("income"/"expense")
  - Lookup by transaction ID
Responds with JSON: either a list of transactions or a single transaction object.
"""
import os
import json
import zmq
from bson.objectid import ObjectId
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi

# Load .env
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI not set in .env")

# MongoDB client with TLS
client = MongoClient(
    MONGO_URI,
    server_api=ServerApi("1"),
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000,
)
try:
    client.admin.command("ping")
    print("Connected to MongoDB")
except Exception as e:
    print("MongoDB ping failed:", e)
    exit(1)

db = client["budgetwise_db"]
transactions = db.transactions

# ZeroMQ setup
ZMQ_ADDR = "tcp://0.0.0.0:5555"
ctx = zmq.Context()
socket = ctx.socket(zmq.REP)
socket.bind(ZMQ_ADDR)
print(f"[Microservice] Listening on {ZMQ_ADDR}...")

while True:
    try:
        req = socket.recv_json()

        # ID lookup
        if "id" in req:
            try:
                oid = ObjectId(req["id"])
                doc = transactions.find_one(
                    {"_id": oid},
                    {"date":1, "type":1, "description":1, "category":1, "amount":1}
                )
                if doc:
                    doc["_id"] = str(doc["_id"])
                    resp = doc
                else:
                    resp = {"error": "Transaction not found"}
            except Exception as exc:
                resp = {"error": f"Invalid id: {exc}"}

        else:
            # Month/type filter (either or both)
            query = {}
            if "month" in req:
                query["date"] = {"$regex": f"^{req['month']}"}
            if "type" in req:
                query["type"] = req["type"]
            if not query:
                resp = {"error": "Provide 'id', 'month', or 'type'"}
            else:
                docs = []
                for d in transactions.find(
                        query,
                        {"date":1, "type":1, "description":1, "category":1, "amount":1}
                    ):
                    d["_id"] = str(d["_id"])
                    docs.append(d)
                resp = docs

        socket.send_json(resp)

    except Exception as e:
        socket.send_json({"error": f"Unexpected error: {e}"})
        continue
