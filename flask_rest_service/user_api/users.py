import os
from flask_rest_service import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature     # To generate the token for email verification
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime


_user_parser =  reqparse.RequestParser()

_user_parser.add_argument('email',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_user_parser.add_argument('password',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_user_parser.add_argument('user_type',
                    type=str,
                    required=False,
                    help="This field cannot be blank."
                    )
_user_parser.add_argument('remember_me',
                    type=str,
                    required=False,
                    help="This field cannot be blank."
                    )

_change_password_parser =  reqparse.RequestParser()

_change_password_parser.add_argument('current_password',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_change_password_parser.add_argument('password',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


class Test(Resource):
     def get(self):
        collections = []
        for collection in mongo.db.list_collection_names():
            collections.append(collection)
        return json.loads(json.dumps(collections, default=json_util.default))


# Registers the user with email and password
class UserRegister(Resource):
    def post(self):
        data = _user_parser.parse_args()
        _hased_password = generate_password_hash(data['password'])      # Password hasing
        user = mongo.db.users.find_one({'email': data['email']})
        if user:
            return {
                "message": "Email already exists in the system."
            }, 409
        id = mongo.db.users.insert({
            'email': data['email'],
            'password':_hased_password,
            'user_type':"UVU",
            'is_verified': False,
            'profile_basic_completion': False,
            'profile_detailed_completion': False,
            'profile_billing_completion': False,
            'logout': True,
            'createdDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection users 
        token = s.dumps(data['email'], salt='email-confirm')
        link = url_for('emailconfirmation', token=token, _external=True)
        msg = Message(
            subject = "Email confirmation for Service-System",
            sender = os.environ['GMAIL_USERNAME'],
            recipients=[data['email']],
            body="Thank you for signing up on Service-System. Please open the verification link to verify your email. Incase you have not setupyour password yourself then please use the temporary password systemserivce12 {}".format(link) 
        )
        mail.send(msg)                                                                                             
        return {"message": "User added successfully! "}, 201


# Email confirmation of the user 
class EmailConfirmation(Resource):
    def get(self, token):
        try:
            email_confirmation = s.loads(token, salt='email-confirm', max_age=600)
            if email_confirmation:
                user = mongo.db.users.find_one({'email': email_confirmation})
                if user:
                    mongo.db.users.update_one({'email': email_confirmation}, {
                        '$set':{
                            'is_verified': True
                        }
                    })
                    
                    return {
                        "message": "User can login now",
                    }, 200
                return {
                    "message": "User not found"
                }, 404
        except SignatureExpired:
            return {"message": "The verification token has expired now. Please register again."}, 401
        except BadTimeSignature:
            return {"message": "The verification token is invalid"}, 401


# After email confirmation user starts to login 
class UserLogin(Resource):
    def post(self):
        data = _user_parser.parse_args()
        user = mongo.db.users.find_one({'email': data['email']})
        if user and check_password_hash(user.get("password"), data['password']):
            if user.get("is_verified"):
                access_token = create_access_token(identity=str(user['_id']), fresh=True)
                refresh_token = create_refresh_token(str(user['_id']))
                return {
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }, 200
            return {
                'message': 'You need to verify your account!'
            }, 401
        return {
            'message': 'Invalid Credentials'
        }, 401

# Check if user_type and user is authenticated and return user type
class CheckUserValidity(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get("user_type") == "SPCAe":
            return {
                "logout": user.get("logout"),
                "isAuthenticated": True,
                "user_type": user.get("user_type"),
                "profile_detailed_completion": user.get("profile_detailed_completion"),
                "profile_basic_completion": user.get("profile_basic_completion"),
                "serviceManagement": user.get("serviceManagement"),
                "clientManagement": user.get("clientManagement")
            }, 200
        if user:
            return {
                "logout": user.get("logout"),
                "isAuthenticated": True,
                "user_type": user.get("user_type"),
                "profile_detailed_completion": user.get("profile_detailed_completion"),
                "profile_basic_completion": user.get("profile_basic_completion"),
            }, 200
        return {
            "isAuthenticated": False,
        }, 401

class ChangePassword(Resource):
    @jwt_required
    def put(self):
        changePasswordData= _change_password_parser.parse_args()
        _hased_password = generate_password_hash(changePasswordData['password'])      # Password hasing
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                    '$set': {
                    'password': _hased_password
                }
            })
            return {"message": "Password updated sucessfully. Please login again."}, 200
        return {
            "message": "User does not exist"
        }, 400

class SerivceProvidersList(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA":
            serviceProviders = []
            for spca in mongo.db.users.find({'user_type': 'SPCA'}):
                serviceProviders.append(spca)
            for sps in mongo.db.users.find({'user_type': 'SPS'}):
                serviceProviders.append(sps)
            return json.loads(json.dumps(serviceProviders, default=json_util.default))
        return {
            "message": "You are not authorized to view service providers"
        }, 403

class ClientsList(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA":
            clients = []
            for cca in mongo.db.users.find({'user_type': 'CCA'}):
                clients.append(cca)
            for cs in mongo.db.users.find({'user_type': 'CS'}):
                clients.append(cs)
            return json.loads(json.dumps(clients, default=json_util.default))
        return {
            "message": "You are not authorized to view clients"
        }, 403