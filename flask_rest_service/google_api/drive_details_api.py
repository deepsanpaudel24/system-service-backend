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

class GoogleCredentialsDetails(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.google_credentials.find_one({'userId': ObjectId(current_user)})
        if user:
            return {"message": "Google Account linked"}, 200
        return { "message": "Google Account not linked"}, 404