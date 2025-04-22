import json
import sys
import os
from pymongo import MongoClient

docker_db = os.environ.get('DOCKER_DB', "false")

if docker_db == "true":
    print("using docker compose db")
    mongo_client = MongoClient("mongo")
else:
    print("using local db")
    mongo_client = MongoClient("localhost")

db = mongo_client["312mmo"]

user_collection = db["users"]
logged_in = db["logged_in"]
# prob need leaderboards and other thing stoed, just add as you go
