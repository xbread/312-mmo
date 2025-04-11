# Imports
from flask import request, make_response, Response
from pymongo import MongoClient
import bcrypt                #Used to encrypt passwords
import uuid                  #Used to generate user ids
import secrets               #Used to generate auth tokens
import hashlib               #Used to hash auth tokens

# Mongo DB info
# DB structure not set yet
mongo_client = MongoClient('localhost')
db = mongo_client['<name>']
user_collection = db['users']

#code for authentication here:

def registration(http_request: request, handler):
    #Make response obj
    registration_response = None
    #Get requested credentials
    requested_credentials = http_request.args
    username = requested_credentials[0]
    password = requested_credentials[1]
    password_isValid = validate_password(password)

    #Find if username is taken
    user_lookup = user_collection.find_one({"username": username})

    #Check lookup first if username is taken or not
    if (user_lookup is not None) and (user_lookup["username"] == username):
        registration_response = Response(response="Username already taken", mimetype="text/plain", status=400)
        registration_response.headers["Content-Type"] = "text/plain; charset=utf-8"

    #Check password is strong enough
    elif not password_isValid:
        registration_response = Response(response="Password is not strong enough", mimetype="text/plain", status=400)
        registration_response.headers["Content-Type"] = "text/plain; charset=utf-8"

    #Otherwise, register user
    else:
        #Generate user id for DB
        user_id = uuid.uuid4()
        user_id = str(user_id)

        #Encode password, generate salt, and hash
        password = password.encode("utf-8")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password, salt)

        image_URL = "public/avatar/default_avatar.png"

        #Insert user in DB
        user_collection.insert_one(
            {"id": user_id, "username": username, "password": password_hash, "imageURL": image_URL})

    handler.request.sendall(registration_response)

def login(http_request: request, handler):
    # Make response obj
    login_response = None
    # Get requested credentials
    requested_credentials = http_request.args
    username = requested_credentials[0]
    password = requested_credentials[1]

    #Find user
    user_lookup = user_collection.find_one({"username" : username})

    if user_lookup is None:
        login_response = Response(response="User by this name does not exist", mimetype="text/plain", status=400)
        login_response.headers["Content-Type"] = "text/plain; charset=utf-8"
    else:
        #Check pw is correct
        password = password.encode("utf-8")
        stored_pass = user_lookup["password"]
        if bcrypt.checkpw(password, stored_pass):
            login_response = Response()

            #Make auth token
            auth_cookie = secrets.token_hex(32)
            hash_cookie = hashlib.sha256(auth_cookie.encode("utf-8")).hexdigest()
            expires = 60 * 60 * 24 * 365 * 10
            login_response.set_cookie("auth-token", value=auth_cookie, max_age=expires, httponly=True)

            #Update user with hashed auth token
            user_collection.update_one(user_lookup, {'$set': {"auth_token": hash_cookie}})
        else:
            login_response = Response(response="Incorrect password", mimetype="text/plain", status=400)
            login_response.headers["Content-Type"] = "text/plain; charset=utf-8"

    handler.request.sendall(login_response)

def logout(http_request: request, handler):
    logout_response = None

    #Check auth token is in cookies
    if ("auth_token" not in http_request.cookies) or (http_request.cookies == ""):
        logout_response = Response(response="Not logged in or missing token", mimetype="text/plain", status=400)
        logout_response.headers["Content-Type"] = "text/plain; charset=utf-8"
    else:
        #Lookup user with auth_cookie
        auth_cookie = http_request.cookies["auth_token"]
        hash_cookie = hashlib.sha256(auth_cookie.encode("utf-8")).hexdigest()
        current_user_lookup = user_collection.find_one({"auth_token": hash_cookie})
        #If no user is found:
        if current_user_lookup is None:
            logout_response = Response(response="Invalid token", mimetype="text/plain", status=400)
            logout_response.headers["Content-Type"] = "text/plain; charset=utf-8"
        #If user is found
        else:
            #Make dummy cookie to remove auth_token
            dummy_cookie = secrets.token_hex(32)

            #Respond w/ 302 and redirect to home
            logout_response = Response(status=302)
            logout_response.set_cookie("auth-token", value=dummy_cookie, max_age=0, httponly=True)
            logout_response.headers["Location"] = "/"

    handler.request.sendall(logout_response)


def validate_password(password: str) -> bool:
    #In order: Length, Lower, Upper, Digit, Spec Char, No Invalid Char
    spec_char_arr = ["!", "@", "#", "$", "%", "^", "&", "(", ")", "-", "_", "="]

    #Len check
    if len(password) < 8:
        return False

    #lowercase check
    for char in password:
        if char.islower():
            break
    else:
        return False

    # uppercase check
    for char in password:
        if char.isupper():
            break
    else:
        return False

    # Digit check
    for char in password:
        if char.isdigit():
            break
    else:
        return False

    # Special character check
    for char in password:
        if char in spec_char_arr:
            break
    else:
        return False

    # No invalid char check
    for char in password:
        if (not char.isalnum()) and (not char in spec_char_arr):
            return False

    return True
