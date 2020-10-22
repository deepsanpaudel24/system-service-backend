import os
from flask import jsonify
from flask_rest_service import app, api, mongo, mail
# from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature     # To generate the token for email verification
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime


_client_parser =  reqparse.RequestParser()

_client_parser.add_argument('email',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

_client_setup_password_parser = reqparse.RequestParser()

_client_setup_password_parser.add_argument('password',
                                            type=str,
                                            required=True,
                                            help="This field cannot be blank"
                                            )
_client_setup_password_parser.add_argument('confirm-password',
                                            type=str,
                                            required=True,
                                            help="This field cannot be blank"
                                            )



s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


# Registers the user with email and password
class ClientRegister(Resource):
    @jwt_required
    def post(self):
        data = _client_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            if user.get("user_type") == "SPCA" or user.get("user_type") == "SPCAe" or user.get("user_type") == "SPS":
                client_existence = mongo.db.users.find_one({'email': data['email']})
                if client_existence:
                    return {"message": "Email already registered in the system"}, 400
                id = mongo.db.users.insert({
                    'email': data['email'],
                    'password':'',
                    'user_type':"CCA",
                    'is_verified': False,
                    'invited_by': ObjectId(current_user),
                    'profile_basic_completion': False,
                    'profile_detailed_completion': False,
                    'profile_billing_completion': True,
                    'logout': True,
                    'createdDate': datetime.today().strftime('%Y-%m-%d')
                })                           # insert the data in the collection users                                                                                              
                return {"message": "Client added successfully! "}, 201
            return {"message": "You are not allowed to add client"}, 403
        return {
            "message": "Failed to add client"
        }, 403

class ClientEmailConfrimation(Resource):
    def post(self):
        data = _client_parser.parse_args()
        token = s.dumps(data['email'], salt='client-email-confirm')
        link_react = "http://localhost:3000/user/client/password-setup/{}".format(token)
        msg = Message(
            subject = "Email confirmation for Service-System",
            sender = os.environ['GMAIL_USERNAME'],
            recipients=[data['email']],
            body="You have been invited on Service-System. Please open the link to verify and setup your account. {}".format(link_react) 
        )
        mail.send(msg)

# Reset password confirmation of the user 
class ClientSetupPassword(Resource):
    def put(self, token):
        try:
            data = _client_setup_password_parser.parse_args()
            setup_password_client = s.loads(token, salt='client-email-confirm', max_age=600)
            if setup_password_client:
                if data['password'] == data['confirm-password']:
                    user = mongo.db.users.find_one({'email': setup_password_client})
                    _hased_password = generate_password_hash(data['password'])      # Password hasing
                    if user:
                        mongo.db.users.update_one({'email': setup_password_client}, {
                            '$set':{
                                'password': _hased_password,
                                'is_verified': True
                            }
                        })
                        return {
                            "message": "Password Updated successfully",
                        }, 200
                    return {
                        "message": "User not found"
                    }, 404
                return { "message": "Password and confirm-password does not match"}
        except SignatureExpired:
            return {"message": "The verification token has expired now. Please reset again."}, 401
        except BadTimeSignature:
            return {"message": "The verification token is invalid"}, 401


class UserClientList(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        clients = []
        for client in mongo.db.users.find({'invited_by': ObjectId(current_user)}).sort("_id", -1):
            clients.append(client)
        return json.loads(json.dumps(clients, default=json_util.default))