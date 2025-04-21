from pymongo import MongoClient
from util.database import user_collection
import hashlib

mongo_client = MongoClient('localhost')
db = mongo_client['312mmo']

def get_username(auth_token):
    if auth_token is not None:
        hash_cookie = hashlib.sha256(auth_token.encode("utf-8")).hexdigest()
        user_lookup = user_collection.find_one({"auth_token": hash_cookie})
        if user_lookup is None:
            return None
        else:
            return user_lookup["username"]
    else:
        return None