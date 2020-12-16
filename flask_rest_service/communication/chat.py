from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, send, emit, join_room, leave_room, disconnect, ConnectionRefusedError
from time import localtime, strftime
# from flask_pymongo import PyMongo
from flask_rest_service import app, api, mongo
from bson.json_util import dumps
import json
import os
import base64
from functools import wraps
from pathlib import Path
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import uuid
from flask_restful import Resource
from datetime import datetime
import bson
from .InitialChatMessage import encrypt_me, decrypt_me, fetch_messages, MESSAGE_FETCH_LIMIT


# Initalize socketio
socketio = SocketIO(app, cors_allowed_origins="*")

# decorators to check if the connected user are authorized


# def get_encrypt_decrypt_key():
#     password_provided = app.secret_key
#     password = password_provided.encode()
#     salt = b'd\x06//\x8b\xb5\x8b\x1dIQ\xfb\x17N\xb3-\xfa'
#     kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
#                      salt=salt, iterations=100000, backend=default_backend())
#     key = base64.urlsafe_b64encode(kdf.derive(password))
#     return key


# def encrypt_me(data):
#     # encrypting message sent by user
#     key = get_encrypt_decrypt_key()
#     msg_encoded = bytes(data, encoding='utf-8')
#     f = Fernet(key)
#     # message_token in byte
#     message_token = f.encrypt(msg_encoded)
#     # message_token in string
#     message_token = message_token.decode()
#     return message_token


# def decrypt_me(token):
#     key = get_encrypt_decrypt_key()
#     f = Fernet(key)
#     # converting token in byte from string and then decrypting
#     decrypted_data = f.decrypt(bytes(token, encoding='utf-8'))
#     return decrypted_data.decode()


# def fetch_messages(room, number_of_message, *args, **kwargs):
#     # getting latest messages and sending to client
#     query_obj = {"room": room}
#     all_messages = mongo.db.messages.find(query_obj).sort(
#         "_id", -1).limit(number_of_message)
#     # cannot loop on bson so, need to dump and load to make python object
#     all_messages = json.loads(dumps(all_messages))

#     decoded_all_messages = []
#     for single_messages in all_messages:
#         message_token = single_messages.get('message')
#         single_messages['message'] = decrypt_me(message_token)
#         decoded_all_messages.append(single_messages)

#     return decoded_all_messages


def chat_head(func):
    @wraps(func)
    def inner_func(data, *args):
        user = mongo.db.users.find_one({"_id": ObjectId(data['userId'])})
        # knowing whether the connected user is able to chat or not
        if user and user['is_verified']:
            if len(args):
                return func(data, *args)
            return func(data)
        else:
            disconnect()
    return inner_func


# Join event for server
@socketio.on('join')
@chat_head
def handel_join(data):
    join_room(data['room'])
    data['message'] = f"{data['username']} has joined {data['room']}."
    socketio.emit("join_status_reply", data, room=data['room'])


# Leave event for server
@socketio.on('leave')
def handel_leave(data):
    leave_room(data['room'])
    context = {
        'username': data['username'],
        'message': f"{data['username']} has left {data['room']}."
    }
    socketio.emit("leave_status_reply", context, room=data['room'])


# Custom message event to send on client side
@socketio.on('send_message')
@chat_head
def handel_send_message(data):

    message_token = encrypt_me(data['message'])
    userId = ObjectId(data['userId'])
    username = data['username']
    room = data['room']
    time = strftime('%b-%d %I:%M%p', localtime())

    # inserting message in database
    _id = mongo.db.messages.insert_one(
        {'room': room, 'message': message_token, 'senderId': userId, 'sender': username, 'created_at': datetime.now().strftime("%B %d, %Y %H:%M:%S"), 'message_type': 'TEXT'})

    message_list = fetch_messages(data['room'], MESSAGE_FETCH_LIMIT)
    data['timestamp'] = time
    data['all_messages'] = message_list[::-1]
    socketio.emit("receive_message", data, room=room)


# Event to handel files uploaded
@socketio.on('file_upload')
@chat_head
def fileUpload(chat_client_data, file_data):
    userId = ObjectId(chat_client_data['userId'])
    username = chat_client_data['username']
    room = chat_client_data['room']

    user = mongo.db.users.find_one({'_id': ObjectId(userId)})
    if user.get('user_type') == "CCA" or user.get('user_type') == "CS":
        userType = "c"
    else:
        userType = "sp"

    # bin_value = base64.b64decode(data['binary'])
    # file_storing_path = "static/images/"
    file_storing_path = app.config['UPLOAD_FOLDER']
    base_path = "http://127.0.0.1:5000/"

    file_name = secure_filename(file_data['name'])
    file_name, extension = file_name.split('.')
    file_name = f"{file_name}-{uuid.uuid4().hex}.{userType}.{extension}"

    with open(f"{file_storing_path}/{file_name}", "wb") as f:
        f.write(file_data['binary'])

    full_file_path_db = '/'.join((f.name).split('/')[1:])
    full_file_path_db = os.path.join(base_path, full_file_path_db)

    # encrypting the location of file
    message_token = encrypt_me(full_file_path_db)
    time = strftime('%b-%d %I:%M%p', localtime())

    # inserting file path in messages collection
    _id = mongo.db.messages.insert_one(
        {'room': room, 'message': message_token, 'senderId': userId, 'sender': username, 'created_at': time, 'message_type': 'MULTIMEDIA'})

    # updating files attribute of case collection--caseId is room
    mongo.db.cases.update_one({'_id': ObjectId(room)}, {
        '$push': {
            'files': full_file_path_db,
        }
    })

    message_list = fetch_messages(
        chat_client_data['room'], MESSAGE_FETCH_LIMIT)

    chat_client_data['timestamp'] = time
    chat_client_data['all_messages'] = message_list[::-1]

    socketio.emit('receive_file', (file_data, chat_client_data),
                  room=room)
