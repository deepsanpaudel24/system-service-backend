import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_restful import Api, reqparse
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp
from flask_pymongo import PyMongo
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature     # To generate the token for email verification
from flask_mail import Mail
from flask_jwt_extended import (
    JWTManager, get_current_user ,create_access_token, create_refresh_token, 
    set_access_cookies, set_refresh_cookies, jwt_required, get_jwt_identity, 
    get_raw_jwt, unset_jwt_cookies
)
from bson.objectid import ObjectId
from flask_rest_service.blacklist import BLACKLIST
import datetime

MONGO_URL ="mongodb+srv://service-system:service-system@cluster0.nheoe.mongodb.net/dbservicesystem?retryWrites=true"
app = Flask(__name__)
cors = CORS(app)
app.secret_key = "service-system"
app.config['MONGO_URI'] = MONGO_URL
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['UPLOAD_FOLDER'] = "flask_rest_service/static/allFiles"
mongo = PyMongo(app)

api = Api(app)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TSL": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "rukshan.shady@gmail.com",
    "MAIL_PASSWORD": "*Roshan222#"
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

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    return decrypted_token['jti'] in BLACKLIST

@jwt.revoked_token_loader
def revoked_token_callback():
    return jsonify({
        'description': 'The token has been revoked',
        'error': 'token_revoked'
    }), 401

@app.route("/api/v1/user/logout", methods=["POST"])
@jwt_required
def LogoutUser():
    current_user = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
    if user:
        mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                '$set': {
                'logout': True 
            }
        })
    jti = get_raw_jwt()['jti']
    BLACKLIST.add(jti)
    resp = jsonify({'logout': True})
    return resp, 200

@app.route("/api/v1/user/change-password", methods=["PUT"])
@jwt_required
def ChangePassword():
    current_password = request.json.get('current_password', None)
    password = request.json.get('password', None)
    _hased_password = generate_password_hash(password)      # Password hasing
    current_user = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
    if user:
        if check_password_hash(user.get("password"), current_password):
            mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                        '$set': {
                        'password': _hased_password
                    }
                })
            jti = get_raw_jwt()['jti']
            BLACKLIST.add(jti)
            resp = jsonify({'logout': True})
            return {"message": "Password updated sucessfully. Please login again."}, 200
        return {"message": "Current password does not match"}, 401
    return {"message": "User does not exist"}, 404

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.

@app.route("/api/v1/user/employee/setup-password/<token>", methods=["PUT"])
def EmployeeSetupPassword(token):
    try:
        data = request.json.get('password', None)
        setup_password_employee = s.loads(token, salt='employee-email-confirm', max_age=600)
        if setup_password_employee:
            user = mongo.db.users.find_one({'email': setup_password_employee})
            _hased_password = generate_password_hash(data)      # Password hasing
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
        refresh_token = create_refresh_token(str(user['_id']))
        resp ={
                'isAuthenticated': True,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        return resp, 200
    return {"message": "User does not exist."}, 404



from flask_rest_service.user_api import (   Test, UserRegister, EmailConfirmation, 
                                            UserLogin, Profile, UpdateUserType, UpdateUserProfileBasic, UpdateUserProfileDetailed, 
                                            UpdateUserProfileBilling, CheckUserValidity, ForgotPassword, ResetPassword,
                                            EmployeeRegister, UserEmployeeList, SerivceProvidersList, ClientsList, EmployeeDetails,
                                            ClientRegister, UserClientList, PeopleRegister, PeopleDetails, EmployeeSetupPassword,
                                            ClientSetupPassword, SendEmailConfirmation, SendEmployeeEmailInvitation, ClientEmailConfrimation,
                                            PeopleInvitationEmail, UpdateUserIntro
                                        )

from flask_rest_service.case_management import (    AddNewCaseRequest, Cases, ClientCases, ClientCasesDetails, ForwardCaseRequest, 
                                                    ServiceProviderCases, ServiceProviderCasesDetails, ReplyCaseRequest,
                                                    CaseProposals, PropsalDetails, ServiceProviderCasesActive, ProposalDetailsForSP,
                                                    EmployeeCaseAssignment, EmployeeCases
                                                )

from flask_rest_service.service_management import Service, ServicesList, ServiceAction, SaViewServicesList

from flask_rest_service.notifications import Notifcations

from flask_rest_service.timers import AddTimer, TotalSpentTime

from flask_rest_service.custom_task import AddCustomTask, CustomTasksDetails

from flask_rest_service.form_generation import IntakeForm

from flask_rest_service.google_api import ( Authorize, OAuth2CallBack, GoogleDriveCreateFile, GoogleDriveFetchFiles, Revoke, ClearCredentials, GoogleCredentialsDetails )



api.add_resource(UserLogin, '/api/v1/user/login')
api.add_resource(CheckUserValidity, '/api/v1/user/validity')
api.add_resource(UserRegister, '/api/v1/user/register')
api.add_resource(SendEmailConfirmation, '/api/v1/user/send-email-confirmation')
api.add_resource(EmailConfirmation, '/user/email/confirm/<token>')
api.add_resource(ForgotPassword, '/api/v1/user/forgot-password')
api.add_resource(ResetPassword, '/api/v1/user/reset-password/confirm/<token>')
api.add_resource(UserEmployeeList, '/api/v1/user/employee/list')
api.add_resource(Profile, '/user/profile')

# User profile type setup 
api.add_resource(UpdateUserType, '/api/v1/user/flask-restful/update/user_type')
api.add_resource(UpdateUserProfileBasic, '/api/v1/user/update/profile/basic')
api.add_resource(UpdateUserProfileDetailed, '/api/v1/user/update/profile/detailed')
api.add_resource(UpdateUserProfileBilling, '/api/v1/user/update/profile/billing')
api.add_resource(UpdateUserIntro, '/api/v1/user/update/intro')

# Employee related APIs
api.add_resource(EmployeeRegister, '/api/v1/user/employee/register')
api.add_resource(SendEmployeeEmailInvitation, '/api/v1/user/employee/send-email-confirmation')
api.add_resource(EmployeeDetails, '/api/v1/employee/<id>')
api.add_resource(EmployeeSetupPassword, '/api/v1/user/employee/setup-password/<token>')
api.add_resource(SerivceProvidersList, '/api/v1/service-providers/list')
api.add_resource(ClientsList, '/api/v1/clients/list')

api.add_resource(AddNewCaseRequest, '/api/v1/case-request')
api.add_resource(Cases, '/api/v1/cases')
api.add_resource(ClientCases, '/api/v1/client-cases')
api.add_resource(ClientCasesDetails, '/api/v1/case/<id>')
api.add_resource(ForwardCaseRequest, '/api/v1/forward/case-request/<id>')
api.add_resource(ServiceProviderCases, '/api/v1/cases-sp')
api.add_resource(ServiceProviderCasesActive, '/api/v1/cases-sp-active')
api.add_resource(ServiceProviderCasesDetails, '/api/v1/case-sp/<id>')
api.add_resource(ReplyCaseRequest, '/api/v1/case-request/reply/<caseId>')
api.add_resource(CaseProposals, '/api/v1/case/proposals/<caseId>')
api.add_resource(PropsalDetails, '/api/v1/proposal/<proposalId>')
api.add_resource(ProposalDetailsForSP, '/api/v1/propsal-sp/<caseId>')
api.add_resource(EmployeeCaseAssignment, '/api/v1/case-assign/<caseId>')
api.add_resource(EmployeeCases, '/api/v1/cases-emp')

api.add_resource(Service, '/api/v1/service')
api.add_resource(ServiceAction, '/api/v1/service/<id>')
api.add_resource(ServicesList, '/api/v1/services')
api.add_resource(SaViewServicesList, '/api/v1/services/<ownerid>')

api.add_resource(ClientRegister, '/api/v1/client/register')
api.add_resource(ClientEmailConfrimation, '/api/v1/client/send-email-confirmation')
api.add_resource(ClientSetupPassword, '/api/v1/user/client/setup-password/<token>')
api.add_resource(UserClientList, '/api/v1/clients')

# Api naming considered for the sencond time from here
api.add_resource(PeopleRegister, '/api/v1/peoples')
api.add_resource(PeopleInvitationEmail, '/api/v1/people/send-email-confirmation')
api.add_resource(PeopleDetails, '/api/v1/peoples/<id>')

api.add_resource(Notifcations, '/api/v1/notifications')

api.add_resource(AddTimer, '/api/v1/timers')
api.add_resource(TotalSpentTime, '/api/v1/total-time/<caseId>')

api.add_resource(AddCustomTask, '/api/v1/tasks')
api.add_resource(CustomTasksDetails, '/api/v1/tasks/<id>')

api.add_resource(IntakeForm, '/api/v1/intake-form')

api.add_resource(GoogleCredentialsDetails, '/api/v1/google-credentials-details')
api.add_resource(Authorize, '/api/v1/authorize')
api.add_resource(OAuth2CallBack, '/api/v1/oauth2callback')
api.add_resource(GoogleDriveCreateFile, '/api/v1/google-create-file')
api.add_resource(GoogleDriveFetchFiles, '/api/v1/google-fetch-files/<folder_name>')
api.add_resource(Revoke, '/api/v1/revoke')
api.add_resource(ClearCredentials, '/api/v1/clear')


