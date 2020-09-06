import os
from flask import Flask, request, jsonify
from flask_restful import Api, reqparse
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from flask_pymongo import PyMongo
from flask_mail import Mail
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies
from bson.objectid import ObjectId

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


@app.route("/user/login", methods=["POST"])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = mongo.db.users.find_one({'email': email})
    if user and check_password_hash(user.get("password"), password):
        if user.get("is_verified"):
            access_token = create_access_token(identity=str(user['_id']), fresh=True)
            refresh_token = create_refresh_token(str(user['_id']))
            # Set the JWT cookies in the response
            resp = jsonify({'login': True})
            set_access_cookies(resp, access_token)
            set_refresh_cookies(resp, refresh_token)
            return resp, 200
    return {"login": False}


from flask_rest_service.user_api import Test, UserRegister, EmailConfirmation, UserLogin, Profile

api.add_resource(UserRegister, '/user/register')
api.add_resource(EmailConfirmation, '/user/email/confirm/<token>')
api.add_resource(UserLogin, '/user/flask-restful/login')
api.add_resource(Profile, '/user/profile')