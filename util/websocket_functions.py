from pymongo import MongoClient
from util.database import user_collection
import hashlib

mongo_client = MongoClient('localhost')
db = mongo_client['312mmo']

def get_username(auth_payload):
    if auth_payload is not None and isinstance(auth_payload, dict):
        auth_token = auth_payload.get("token")
        if auth_token:
            hash_cookie = hashlib.sha256(auth_token.encode("utf-8")).hexdigest()
            user_lookup = user_collection.find_one({"auth_token": hash_cookie})
            if user_lookup is None:
                return None
            else:
                return user_lookup["username"]
    return None
