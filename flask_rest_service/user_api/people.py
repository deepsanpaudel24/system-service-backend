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


_people_parser =  reqparse.RequestParser()

_people_parser.add_argument('email',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

_updatePeople_parser =  reqparse.RequestParser()

_updatePeople_parser.add_argument('deactivate',
                    type=bool,
                    required=False
                    )

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


class PeopleRegister(Resource):
    @jwt_required
    def post(self):
        data = _people_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            if user.get("user_type") == "SA" or user.get("user_type") == "SAe":
                people_exist = mongo.db.users.find_one({'email': data['email']})
                if people_exist:
                    return {"message": "Email already registered in the system"}, 400
                id = mongo.db.users.insert({
                    'email': data['email'],
                    'password':'',
                    'user_type':"UVU",
                    'is_verified': False,
                    'invited_by': ObjectId(current_user),
                    'profile_basic_completion': False,
                    'profile_detailed_completion': False,
                    'profile_billing_completion': False,
                    'logout': True,
                    'createdDate': datetime.today().strftime('%Y-%m-%d')
                })                           # insert the data in the collection users                                                                                              
                return {"message": "People added successfully! "}, 201
            return {"message": "You are not allowed to add people"}, 403
        return {
            "message": "Failed to add People"
        }, 403

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        peoples = []
        for people in mongo.db.users.find( { "user_type": { "$nin": ["SA", "SAe"] } } ).sort("_id", -1):
            peoples.append(people)
        return json.loads(json.dumps(peoples, default=json_util.default))


class PeopleInvitationEmail(Resource):
    def post(self):
        data = _people_parser.parse_args()
        token = s.dumps(data['email'], salt='people-email-confirm')
        link_react = "http://localhost:3000/user/people/password-setup/{}".format(token)
        msg = Message(
            subject = "Email confirmation for Service-System",
            sender ="eriksentury470@gmail.com",
            recipients=[data['email']],
            body="You have been invited on Service-System by the system admin. Please open the link to verify and setup your account. {}".format(link_react) 
        )
        mail.send(msg)
        return {"message": "Inviation mail sent sucessfully"}

class PeopleDetails(Resource):
    @jwt_required
    def put(self, id):
        data= _updatePeople_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "SAe":
            mongo.db.users.update_one({'_id': ObjectId(id)}, {
                        '$set': {
                        'deactivate': data['deactivate'],
                    }
                })
            return {
                "message": "People account status updated sucessfully"
            }, 200

    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "SAe":
            people_details = mongo.db.users.find_one({'_id': ObjectId(id)})
            return json.loads(json.dumps(people_details, default=json_util.default))