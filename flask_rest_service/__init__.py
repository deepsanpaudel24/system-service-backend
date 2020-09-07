import os
from flask import Flask, request, jsonify
from flask_restful import Api, reqparse
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from flask_pymongo import PyMongo
from flask_mail import Mail
from flask_jwt_extended import JWTManager, get_current_user ,create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies, jwt_required, get_jwt_identity
from bson.objectid import ObjectId
import datetime

MONGO_URL = os.environ.get('MONGO_URI')

app = Flask(__name__)
app.secret_key = "service-system"
app.config['MONGO_URI'] = MONGO_URL
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
mongo = PyMongo(app)

api = Api(app)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TSL": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": os.environ['GMAIL_USERNAME'],
    "MAIL_PASSWORD": os.environ['GMAIL_PASSWORD']
}
app.config.update(mail_settings)
mail = Mail(app)

jwt = JWTManager(app)

@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    user = mongo.db.users.find_one({'_id': ObjectId(identity)})
    return {
        'user_type': user["user_type"]
    }

@jwt.expired_token_loader
def expired_token_callback():
    return jsonify({
        'message': 'The token has expired'
    }), 401

@app.route("/user/login", methods=["POST"])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = mongo.db.users.find_one({'email': email})
    if user and check_password_hash(user.get("password"), password):
        if user.get("is_verified"):
            expires = datetime.timedelta(days=1)
            access_token = create_access_token(identity=str(user['_id']), fresh=True, expires_delta=expires)
            refresh_token = create_refresh_token(str(user['_id']))
            # Set the JWT cookies in the response
            resp = jsonify({
                'login': True,
                'user_type': user.get("user_type"),
                'profile_basic_completion':user.get("profile_basic_completion"),
                'profile_detailed_completion':user.get("profile_detailed_completion"),
                'profile_billing_completion':user.get("profile_billing_completion")
            })
            set_access_cookies(resp, access_token)
            set_refresh_cookies(resp, refresh_token)
            return resp, 200
        return {
                'message': 'You need to verify your account!'
            }, 401
    return {
            'message': 'Invalid Credentials'
        }, 401

@app.route("/api/v1/user/update/user_type", methods=["PUT"])
@jwt_required
def UpdateUserType():
    user_type = request.json.get('user_type', None)
    if not user_type:
        return {
            'message': 'User type is empty'
        }
    current_user = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
    if user:
        mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                '$set': {
                'user_type': user_type
            }
        })
        expires = datetime.timedelta(days=1)
        access_token = create_access_token(identity=current_user, fresh=True, expires_delta=expires)
        resp = jsonify({
                'isAuthenticated': True
            })
        set_access_cookies(resp, access_token)
        return {"message": "User type updated successfully"}, 200
    return {"message": "User does not exist."}, 404


from flask_rest_service.user_api import Test, UserRegister, EmailConfirmation, UserLogin, Profile, UpdateUserType, UpdateUserProfileBasic, UpdateUserProfileDetailed, UpdateUserProfileBilling

api.add_resource(UserRegister, '/user/register')
api.add_resource(EmailConfirmation, '/user/email/confirm/<token>')
api.add_resource(UserLogin, '/user/flask-restful/login')
api.add_resource(Profile, '/user/profile')
api.add_resource(UpdateUserType, '/api/v1/user/flask-restful/update/user_type')
api.add_resource(UpdateUserProfileBasic, '/api/v1/user/update/profile/basic')
api.add_resource(UpdateUserProfileDetailed, '/api/v1/user/update/profile/detailed')
api.add_resource(UpdateUserProfileBilling, '/api/v1/user/update/profile/billing')