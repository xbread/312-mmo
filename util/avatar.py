from flask import request
from pymongo import MongoClient
from util.database import user_collection, logged_in
import uuid
import hashlib
from app import ALLOWED_EXTENSIONS, UPLOAD_FOLDER

ALLOWED_TYPES = ["image/png", "image/jpeg"]

Ext_Map = {"image/png" : "png", "image/jpeg": "jpg"}

mongo_client = MongoClient('localhost')
db = mongo_client['312mmo']

def user_valid(http_request: request):
    auth_token = http_request.cookies["auth_token"]
    hashed_token = hashlib.sha256(auth_token.encode("utf-8")).hexdigest()
    current_user_lookup = user_collection.find_one({"auth_token": hashed_token})
    if current_user_lookup is None:
        return current_user_lookup["username"]
    else:
        return None

def valid_extension(file):
    filename = file.filename
    if ('.' in filename) and (filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
        file_type = file.content_type
        if file_type in ALLOWED_TYPES:
            return True
    return False

def get_extension_type(file):
    return Ext_Map[file.content_type]

def change_avatar(file, username: str, extension: str):
    file_id = str(uuid.uuid4())
    filename = file_id + "." + extension
    file_path = UPLOAD_FOLDER + filename
    file_write = open(file_path, "wb")
    file_write.write(file.read())
    user_lookup = user_collection.find_one({"username": username})
    user_collection.update_one(user_lookup, {"$set": {"imageURL": file_path}})