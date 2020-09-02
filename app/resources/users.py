import os
from flask_restful import Resource, request, reqparse, url_for
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature     # To generate the token for email verification
from flask_jwt_extended import create_access_token, create_refresh_token 
from bson.objectid import ObjectId
import json
from bson import json_util
from db import mongo
from mail_sender import mail

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

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.

# Registers the user with email and password
class UserRegister(Resource):
    def post(self):
        data = _user_parser.parse_args()
        _hased_password = generate_password_hash(data['password'])      # Password hasing
        user = mongo.db.users.find_one({'email': data['email']})
        if user:
            return {
                "message": "Email already exists in the system."
            }
        id = mongo.db.users.insert({
            'email': data['email'],
            'password':_hased_password,
            'user_type':data['user_type'],
            'is_verified': False
        })                           # insert the data in the collection users 
        token = s.dumps(data['email'], salt='email-confirm')
        link = url_for('emailconfirmation', token=token, _external=True)
        msg = Message(
            subject = "Email confirmation for Service-System",
            sender = os.environ['GMAIL_USERNAME'],
            recipients=[data['email']],
            body="Thank you for signing up on Service-System. Please open the verification link to verify your email. {}".format(link) 
        )
        mail.send(msg)                                                                                             
        return {"message": "User added successfully! "}, 409


# Email confirmation of the user 
class EmailConfirmation(Resource):
    def get(self, token):
        try:
            email_confirmation = s.loads(token, salt='email-confirm', max_age=120)
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
                    }
                return {
                    "message": "User not found"
                }
        except SignatureExpired:
            return {"message": "The verification token has expired now. Please register again."}
        except BadTimeSignature:
            return {"message": "The verification token is invalid"}


# After email confirmation user starts to login 
class UserLogin(Resource):
    def post(self):
        data = _user_parser.parse_args()
        user = mongo.db.users.find_one({'email': data['email']})
        if user and check_password_hash(user.get("password"), data['password']):
            access_token = create_access_token(identity=str(user['_id']), fresh=True)
            refresh_token = create_refresh_token(str(user['_id']))
            return {
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200
        return {
            'message': 'Invalid Credentials'
        }, 200