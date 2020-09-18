import os
from flask import jsonify
from flask_rest_service import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature     # To generate the token for email verification
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util


_employee_parser =  reqparse.RequestParser()

_employee_parser.add_argument('email',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

_employee_setup_password_parser = reqparse.RequestParser()

_employee_setup_password_parser.add_argument('password',
                                            type=str,
                                            required=True,
                                            help="This field cannot be blank"
                                            )

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


# Registers the user with email and password
class EmployeeRegister(Resource):
    @jwt_required
    def post(self):
        data = _employee_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            if user.get("user_type") == "SPCA" or user.get("user_type") == "CCA" or user.get("user_type") == "SA":
                employee_existence = mongo.db.users.find_one({'email': data['email']})
                if employee_existence:
                    return {"message": "Email already registered in the system"}, 400
                id = mongo.db.users.insert({
                    'email': data['email'],
                    'password':'',
                    'user_type':user.get("user_type") + "e",
                    'is_verified': False,
                    'owner': ObjectId(current_user),
                    'profile_basic_completion': False,
                    'profile_detailed_completion': True,
                    'profile_billing_completion': True,
                    'logout': True
                })                           # insert the data in the collection users 
                token = s.dumps(data['email'], salt='employee-email-confirm')
                link_react = "http://localhost:3000/user/employee/password-setup/{}".format(token)
                msg = Message(
                    subject = "Email confirmation for Service-System",
                    sender = os.environ['GMAIL_USERNAME'],
                    recipients=[data['email']],
                    body="You have been invited on Service-System. Please open the link to verify setup your account. {}".format(link_react) 
                )
                mail.send(msg)                                                                                             
                return {"message": "Employee added successfully! "}, 201
            return {"message": "You are not allowed to add employee"}, 403
        return {
            "message": "Failed to add employee"
        }, 403

class UserEmployeeList(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        employees = []
        for emp in mongo.db.users.find({'owner': ObjectId(current_user)}):
            employees.append(emp)
        return json.loads(json.dumps(employees, default=json_util.default))


# Reset password confirmation of the user 
class EmployeeSetupPassword(Resource):
    def post(self, token):
        try:
            data = _employee_setup_password_parser.parse_args()
            setup_password_employee = s.loads(token, salt='employee-email-confirm', max_age=600)
            if setup_password_employee:
                user = mongo.db.users.find_one({'email': setup_password_employee})
                _hased_password = generate_password_hash(data['password'])      # Password hasing
                if user:
                    mongo.db.users.update_one({'email': setup_password_employee}, {
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
        except SignatureExpired:
            return {"message": "The verification token has expired now. Please reset again."}, 401
        except BadTimeSignature:
            return {"message": "The verification token is invalid"}, 401