from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection
mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client.flask_db
collection = db.data


# Root endpoint
@app.route("/")
def index():
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"


# Data endpoint
@app.route("/data", methods=["GET", "POST"])
def data():
    if request.method == "POST":
        data = request.get_json()
        collection.insert_one(data)
        return jsonify({"status": "Data inserted"}), 201

    if request.method == "GET":
        data = list(collection.find({}, {"_id": 0}))
        return jsonify(data), 200


# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
