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
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import bson
from bson.codec_options import CodecOptions




# Initalize socketio
socketio = SocketIO(app, cors_allowed_origins="*")

# decorators to check if the connected user are authorized


def get_encrypt_decrypt_key():
    password_provided = app.secret_key
    password = password_provided.encode()
    salt = b'd\x06//\x8b\xb5\x8b\x1dIQ\xfb\x17N\xb3-\xfa'
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=100000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


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
    # context = { this is comment to just for other logic
    #     'username':data['username'],
    #     'message':f"{data['username']} has joined {data['room']}."
    # }
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
    #encrypting message sent by user
    key = get_encrypt_decrypt_key()
    msg_encoded =data['message'].encode()
    f = Fernet(key)
    message = f.encrypt(msg_encoded)
    
    userId = ObjectId(data['userId'])
    username = data['username']
    room = data['room']
    time = strftime('%b-%d %I:%M%p', localtime())

    # inserting message in database
    _id = mongo.db.messages.insert_one(
        {'room': room, 'message': message, 'senderId': userId, 'sender': username, 'created_at': datetime.now().strftime("%B %d, %Y %H:%M:%S"), 'message_type': 'TEXT'})
    # getting latest messages and sending to client
    query_obj = {"room": data['room']}
    all_messages = mongo.db.messages.find(query_obj).sort("_id", -1).limit(5)
    #all_messages = bson.BSON(all_messages).decode()
    # decrypt all the messages and then send it to data['all_messages]
    all_messages = json.loads(dumps(all_messages))
    decoded_all_messages = []
    for single_messages in all_messages:
        s_message = single_messages.get('message')
        # print("type of s_message is", type(s_message['$binary']))
        decrypted_data = f.decrypt(b"f'{s_message['$binary']}'")
        single_messages['message'] = decrypted_data.decode()
        decoded_all_messages.append(single_messages)

    data['timestamp'] = time
    data['all_messages'] = decoded_all_messages[::-1]
    socketio.emit("receive_message", data, room=data['room'])

# Event to handel files uploaded


@socketio.on('file_upload')
@chat_head
def fileUpload(chat_client_data, file_data):
    # bin_value = base64.b64decode(data['binary'])
    # file_storing_path = "static/images/"
    file_storing_path = app.config['UPLOAD_FOLDER']
    base_path = "http://127.0.0.1:5000/"

    file_name = secure_filename(file_data['name'])
    file_name, extension = file_name.split('.')
    file_name = f"{file_name}-{uuid.uuid4().hex}.{extension}"

    with open(f"{file_storing_path}/{file_name}", "wb") as f:
        f.write(file_data['binary'])

    full_file_path_db = '/'.join((f.name).split('/')[1:])
    full_file_path_db = os.path.join(base_path, full_file_path_db)
    userId = ObjectId(chat_client_data['userId'])
    username = chat_client_data['username']
    message = full_file_path_db
    room = chat_client_data['room']
    time = strftime('%b-%d %I:%M%p', localtime())

    _id = mongo.db.messages.insert_one(
        {'room': room, 'message': message, 'senderId': userId, 'sender': username, 'created_at': time, 'message_type': 'MULTIMEDIA'})

    query_obj = {"room": chat_client_data['room']}
    all_messages = mongo.db.messages.find(query_obj).sort("_id", -1).limit(5)
    chat_client_data['timestamp'] = time
    chat_client_data['all_messages'] = json.loads(dumps(all_messages))[::-1]

    socketio.emit('receive_file', (file_data, chat_client_data),
                  room=chat_client_data['room'])


