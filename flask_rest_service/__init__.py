import os
from flask import Flask
from flask_restful import Api
from flask_pymongo import PyMongo
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from bson.objectid import ObjectId

MONGO_URL = os.environ.get('MONGO_URI')

app = Flask(__name__)
app.secret_key = "service-system"
app.config['MONGO_URI'] = MONGO_URL
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

from flask_rest_service.user_api import Test, UserRegister, EmailConfirmation, UserLogin

api.add_resource(UserRegister, '/user/register')
api.add_resource(EmailConfirmation, '/user/email/confirm/<token>')
api.add_resource(UserLogin, '/user/login')