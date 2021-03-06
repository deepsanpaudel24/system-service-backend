import os
from flask import jsonify
from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature     # To generate the token for email verification
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime

def InsertNotifications(*args, **kwargs):
    id = mongo.db.notifications.insert({ 
            'title': kwargs['title'],
            'sender': kwargs['sender'],
            'receiver': kwargs['receiver'],
            'status': 'unread',
            'link': kwargs['link'],
            'createdDate': datetime.today().strftime('%Y-%m-%d')
    })

class Notifications(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        notify_list = []
        for notify in mongo.db.notifications.find( {"$and": [ {'receiver': ObjectId(current_user)}, {'status': 'unread'} ]} ).sort("_id", -1).limit(7):
            notify_list.append(notify)
        return json.loads(json.dumps(notify_list, default=json_util.default))

# To set the notifications as read
class ChangeNotificationStatus(Resource):
    @jwt_required
    def put(self, notificationId):
        mongo.db.notifications.update_one({'_id': ObjectId(notificationId)}, {
                    '$set': {
                    'status': "read"
                }
            })
        return { "message": "Notification marked read"}, 200