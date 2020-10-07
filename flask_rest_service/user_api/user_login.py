import os
from flask import jsonify
from flask_rest_service import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature     # To generate the token for email verification
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
import datetime

_login_parser =  reqparse.RequestParser()

_login_parser.add_argument('email',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_login_parser.add_argument('password',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

class UserLogin(Resource):
    def post(self):
        data = _login_parser.parse_args()
        user = mongo.db.users.find_one({'email': data['email']})
        if user and check_password_hash(user.get("password"), data['password']):
            if user.get("is_verified"):
                expires = datetime.timedelta(days=1)
                access_token = create_access_token(identity=str(user['_id']), fresh=True, expires_delta=expires)
                refresh_token = create_refresh_token(str(user['_id']))
                resp ={
                    'login': True,
                    'user_type': user.get("user_type"),
                    'profile_basic_completion':user.get("profile_basic_completion"),
                    'profile_detailed_completion':user.get("profile_detailed_completion"),
                    'profile_billing_completion':user.get("profile_billing_completion"),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
                return resp, 200
            return {
                "message": "You need to verify your account"
            }, 403
        return {
            "message": "Invalid credentials"
        }, 403
