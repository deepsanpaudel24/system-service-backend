import os
from flask import Flask, url_for
from flask_restful import Api
from flask_pymongo import PyMongo
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from bson.objectid import ObjectId

from app.resources.landingpage import LandingPage
from app.resources.users import UserRegister, EmailConfirmation, UserLogin

app= Flask(__name__)
app.secret_key = "secret_key"
app.config['MONGO_URI'] = "mongodb://localhost:27017/flask-mongo-test"
#app.config['MONGO_URI'] = "mongodb+srv://service-system:service-system@cluster0.nheoe.mongodb.net/test"
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
mongo = PyMongo(app)
api = Api(app)

jwt = JWTManager(app)

@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    user = mongo.db.users.find_one({'_id': ObjectId(identity)})
    return {
        'user_type': user["user_type"]
    }

api.add_resource(LandingPage, '/')
api.add_resource(UserRegister, '/user/register')
api.add_resource(EmailConfirmation, '/user/email/confirm/<token>')
api.add_resource(UserLogin, '/user/login')

