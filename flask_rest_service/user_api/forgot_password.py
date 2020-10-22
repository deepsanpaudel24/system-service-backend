import os
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

_forgot_password_parser = reqparse.RequestParser()

_forgot_password_parser.add_argument('email',
                                    type=str,
                                    required=True,
                                    help="This field cannot be blank"
                                    )

_reset_password_parser = reqparse.RequestParser()

_reset_password_parser.add_argument('password',
                                    type=str,
                                    required=True,
                                    help="This field cannot be blank"
                                    )

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


# Forgot password
class ForgotPassword(Resource):
    def post(self):
        data = _forgot_password_parser.parse_args()
        user = mongo.db.users.find_one({'email': data['email']})
        if user:
            token = s.dumps(data['email'], salt='forgot-password-confirm')
            link = url_for('resetpassword', token=token, _external=True)
            link_react = "http://localhost:3000/user/reset-password/{}".format(token)
            msg = Message(
                subject = "Password reset link for Service-System",
                sender = os.environ['GMAIL_USERNAME'],
                recipients=[data['email']],
                body="Please open this link and fill up the new password to recover your account {}".format(link_react) 
            )
            mail.send(msg)                                                                                             
            return {"message": "Password reset link sent! "}, 200
        return {
            "message": "Email does not exist in the system"
        }, 401


# Reset password confirmation of the user 
class ResetPassword(Resource):
    def post(self, token):
        try:
            data = _reset_password_parser.parse_args()
            reset_password_email = s.loads(token, salt='forgot-password-confirm', max_age=600)
            if reset_password_email:
                user = mongo.db.users.find_one({'email': reset_password_email})
                _hased_password = generate_password_hash(data['password'])      # Password hasing
                if user:
                    mongo.db.users.update_one({'email': reset_password_email}, {
                        '$set':{
                            'password': _hased_password
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