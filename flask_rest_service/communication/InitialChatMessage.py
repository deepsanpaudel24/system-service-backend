from flask_rest_service import app, api, mongo
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
import base64
from bson.json_util import dumps
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


MESSAGE_FETCH_LIMIT = 10


def get_encrypt_decrypt_key():
    password_provided = app.secret_key
    password = password_provided.encode()
    salt = b'd\x06//\x8b\xb5\x8b\x1dIQ\xfb\x17N\xb3-\xfa'
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=100000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt_me(data):
    # encrypting message sent by user
    key = get_encrypt_decrypt_key()
    msg_encoded = bytes(data, encoding='utf-8')
    f = Fernet(key)
    # message_token in byte
    message_token = f.encrypt(msg_encoded)
    # message_token in string
    message_token = message_token.decode()
    return message_token


def decrypt_me(token):
    key = get_encrypt_decrypt_key()
    f = Fernet(key)
    # converting token in byte from string and then decrypting
    decrypted_data = f.decrypt(bytes(token, encoding='utf-8'))
    return decrypted_data.decode()


def fetch_messages(room, number_of_message, offset=0):
    # getting latest messages and sending to client
    query_obj = {"room": room}
    if offset:
        all_messages = mongo.db.messages.find(query_obj).sort(
            "_id", -1).limit(number_of_message).skip(offset)
    else:
        all_messages = mongo.db.messages.find(query_obj).sort(
        "_id", -1).limit(number_of_message)

    # cannot loop on bson so, need to dump and load to make python object
    all_messages = json.loads(dumps(all_messages))

    decoded_all_messages = []
    for single_messages in all_messages:
        message_token = single_messages.get('message')
        single_messages['message'] = decrypt_me(message_token)
        decoded_all_messages.append(single_messages)

    return decoded_all_messages


class InitialChatMessage(Resource):
    @jwt_required
    def get(self, room):
        current_user = get_jwt_identity()
        message_list = fetch_messages(room, MESSAGE_FETCH_LIMIT)
        return message_list[::-1]


class OldChatMessages(Resource):
    @jwt_required
    def post(self, room):
        current_user = get_jwt_identity()
        data = request.get_json()
        count = data['count']
        offset = count*MESSAGE_FETCH_LIMIT
        message_list = fetch_messages(room, MESSAGE_FETCH_LIMIT, offset)
        return message_list[::-1]