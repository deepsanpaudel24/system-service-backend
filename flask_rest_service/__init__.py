import os
from flask import Flask, request, jsonify, make_response, redirect, abort, send_from_directory
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
from datetime import datetime, timedelta
import uuid
# For webscoket 
from flask_socketio import SocketIO, send

MONGO_URL ="mongodb+srv://service-system:service-system@cluster0.nheoe.mongodb.net/dbservicesystem?retryWrites=true"
app = Flask(__name__)
cors = CORS(app)
app.secret_key = "service-system"
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['MONGO_URI'] = MONGO_URL
app.config['FRONTEND_DOMAIN'] = "http://localhost:3000"
app.config['JWT_BLACKLIST_ENABLED'] = True

# Only allow JWT cookies to be sent over https. In production, this
# should likely be True
# app.config['JWT_COOKIE_SECURE'] = True

app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['UPLOAD_FOLDER'] = "flask_rest_service/static/allFiles"
app.config['UPLOAD_FOLDER_VIDEO'] = "flask_rest_service/static/videos"
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['MAX_TABLE_ROWS'] = 10
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

@socketio.on('my_event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

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

@app.route("/api/v1/user/login", methods=["POST"])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = mongo.db.users.find_one({'email': email})
    if user and check_password_hash(user.get("password"), password):
        if user.get("is_verified"):
            if not datetime.strptime(user.get("expiryDate"), '%Y-%m-%d') < datetime.today() :
                if not user.get("deactivate"):
                    expires = timedelta(days=1)
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
                    if user:
                        mongo.db.users.update_one({'email': email}, {
                                '$set': {
                                'logout': False 
                            }
                        })
                    return resp, 200
                return {
                    'message': 'Your account has been deactivated. Please contact System admin.'
                }, 403
            return {
                'message': 'Your account has expired. Please contact System admin.'
            }, 403
        return {
                'message': 'You need to verify your account!'
            }, 401
    return {
            'message': 'Invalid Credentials'
        }, 401

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
    unset_jwt_cookies(resp)
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
            unset_jwt_cookies(resp)
            return {"message": "Password updated sucessfully. Please login again."}, 200
        return {"message": "Current password does not match"}, 401
    return {"message": "User does not exist"}, 404

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


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
        expires = timedelta(days=1)
        access_token = create_access_token(identity=current_user, fresh=True, expires_delta=expires)
        resp = jsonify({
                'isAuthenticated': True
            })
        set_access_cookies(resp, access_token)
        return {"message": "User type updated successfully"}, 200
    return {"message": "User does not exist."}, 404
        

@app.route("/static/allFiles/<filename>", methods=["GET", "POST"])
@jwt_required
def SecureStaticAssest(filename):
    data= request.get_json()
    caseId = data['caseId']
    case_details = mongo.db.cases.find_one({'_id': ObjectId(caseId)})
    current_user = get_jwt_identity()
    listOfUserId = []
    listOfUserId.append(case_details.get('serviceProvider'))
    listOfUserId.append(case_details.get('client'))
    print(current_user, 'this is curret users')
    if case_details.get('assigned_employee_list'):
        listOfUserId.extend(case_details.get('assigned_employee_list'))

    if case_details.get('status') != 'On-progress':
        if case_details.get('forwardTo'):
            listOfUserId.extend(case_details.get('forwardTo'))
    
    if ObjectId(current_user) in listOfUserId:
            BASE_DIR = os.path.dirname(__file__)
            assest_folder = os.path.join(BASE_DIR, 'static/allFiles')
            return send_from_directory(assest_folder, filename, as_attachment=True), 200
    else:
        abort(403)



from flask_rest_service.user_api import (   Test, UserRegister, EmailConfirmation, 
                                            UserLogin, Profile, UpdateUserType, UpdateUserProfileBasic, UpdateUserProfileDetailed, 
                                            UpdateUserProfileBilling, CheckUserValidity, ForgotPassword, ResetPassword,
                                            EmployeeRegister, UserEmployeeList, SerivceProvidersList, ClientsList, EmployeeDetails,
                                            ClientRegister, UserClientList, PeopleRegister, PeopleDetails, EmployeeSetupPassword,
                                            ClientSetupPassword, SendEmailConfirmation, SendEmployeeEmailInvitation, ClientEmailConfrimation,
                                            PeopleInvitationEmail, UpdateUserIntro, ProfileDetails, SendClientsIntakeForm, ClientDetails, 
                                            ShowFillUpFormForClient, InsertClientIntakeFormValues, ClientIntakeFormFilledDetails, 
                                            ProfileSettingUpdate, ProfileIntroductionUpdate, SPClientCases, CreateClientCase, PeopleSetupPassword,
                                            PeopleCases, UpdateCommission, PeopleList, ChildAccountList, UpdateExpiryDate
                                        )

from flask_rest_service.case_management import (    AddNewCaseRequest, Cases, ClientCases, ClientCasesDetails, ForwardCaseRequest, 
                                                    ServiceProviderCases, ServiceProviderCasesDetails, ReplyCaseRequest,
                                                    CaseProposals, PropsalDetails, ServiceProviderCasesActive, ProposalDetailsForSP,
                                                    EmployeeCaseAssignment, EmployeeCases, UploadContractPaper, ContractDetails, ConfirmContractPaper,
                                                    UpdateRelatedDocuments, DeleteRelatedDocuments, EmployeeCasesForSP, UndoCaseForward,
                                                    RequestCaseCompletion, ConfirmCaseCompletion
                                                )

from flask_rest_service.service_management import Service, ServicesList, ServiceAction, SaViewServicesList

from flask_rest_service.notifications import Notifications, ChangeNotificationStatus

from flask_rest_service.timers import AddTimer, TotalSpentTime, CaseTimersList

from flask_rest_service.custom_task import AddCustomTask, CustomTasksDetails, CustomTasksList

from flask_rest_service.form_generation import IntakeForm, IntakeFormList, IntakeFormDetails

from flask_rest_service.google_api import ( Authorize, OAuth2CallBack, GoogleDriveCreateFile, GoogleDriveFetchFiles, Revoke, ClearCredentials, GoogleCredentialsDetails )

from flask_rest_service.communication import socketio, InitialChatMessage, OldChatMessages

from flask_rest_service.payment_module import ( create_checkout_session, Webhook, Onboard_user, Onboard_user_refresh, TransferInfo, Transfer, 
                                                create_subscription_checkout_session, CheckoutTransactions, ClientCaseTransactions, SATransactions,
                                                SACaseTransactions, UserStripeAccInfo, SPTransactions, SPCaseTransactions, SPStripeAccInfo
                                            )



#api.add_resource(UserLogin, '/api/v1/user/login')
api.add_resource(CheckUserValidity, '/api/v1/user/validity')
api.add_resource(UserRegister, '/api/v1/user/register')
api.add_resource(SendEmailConfirmation, '/api/v1/user/send-email-confirmation')
api.add_resource(EmailConfirmation, '/user/email/confirm/<token>')
api.add_resource(ForgotPassword, '/api/v1/user/forgot-password')
api.add_resource(ResetPassword, '/api/v1/user/reset-password/confirm/<token>')
api.add_resource(UserEmployeeList, '/api/v1/user/employee/list/<int:page>')
api.add_resource(PeopleList, '/api/v1/peoples/list/<int:page>')
api.add_resource(ChildAccountList, '/api/v1/people/child-account/<id>/<int:page>')
api.add_resource(Profile, '/user/profile')
api.add_resource(ProfileDetails, '/api/v1/user/profile-details')
api.add_resource(ProfileSettingUpdate, '/api/v1/user/profile-setting')
api.add_resource(ProfileIntroductionUpdate, '/api/v1/user/profile-introduction')

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
api.add_resource(Cases, '/api/v1/cases/<int:page>')
api.add_resource(ClientCases, '/api/v1/client-cases/<int:page>')
api.add_resource(ClientCasesDetails, '/api/v1/case/<id>')
api.add_resource(UndoCaseForward, '/api/v1/case-undo/<id>')
api.add_resource(ForwardCaseRequest, '/api/v1/forward/case-request/<id>')
api.add_resource(ServiceProviderCases, '/api/v1/cases-sp/<int:page>')
api.add_resource(ServiceProviderCasesActive, '/api/v1/cases-sp-active')
api.add_resource(ServiceProviderCasesDetails, '/api/v1/case-sp/<id>')
api.add_resource(ReplyCaseRequest, '/api/v1/case-request/reply/<caseId>')
api.add_resource(CaseProposals, '/api/v1/case/proposals/<caseId>')
api.add_resource(PropsalDetails, '/api/v1/proposal/<proposalId>')
api.add_resource(ProposalDetailsForSP, '/api/v1/propsal-sp/<caseId>')
api.add_resource(EmployeeCaseAssignment, '/api/v1/case-assign/<caseId>')
api.add_resource(EmployeeCases, '/api/v1/case-emp/<int:page>')
api.add_resource(EmployeeCasesForSP, '/api/v1/case-emp/<id>/<int:page>')
api.add_resource(UploadContractPaper, '/api/v1/case-contract/<caseId>')
api.add_resource(ContractDetails, '/api/v1/contract/<caseId>')
api.add_resource(ConfirmContractPaper, '/api/v1/contract-confirm/<caseId>')
api.add_resource(UpdateRelatedDocuments, '/api/v1/case/documents/<id>')
api.add_resource(DeleteRelatedDocuments, '/api/v1/case/docs-remove/<id>')
api.add_resource(CreateClientCase, '/api/v1/sp-client/create-case/<clientId>')
api.add_resource(RequestCaseCompletion, '/api/v1/request-case-completion/<id>')
api.add_resource(ConfirmCaseCompletion, '/api/v1/confirm-case-completion/<id>')

api.add_resource(Service, '/api/v1/service')
api.add_resource(ServiceAction, '/api/v1/service/<id>')
api.add_resource(ServicesList, '/api/v1/services/<int:page>')
api.add_resource(SaViewServicesList, '/api/v1/services/<ownerid>')

api.add_resource(ClientRegister, '/api/v1/client/register')
api.add_resource(ClientEmailConfrimation, '/api/v1/client/send-email-confirmation')
api.add_resource(ClientSetupPassword, '/api/v1/user/client/setup-password/<token>')
api.add_resource(UserClientList, '/api/v1/clients/<int:page>')
api.add_resource(ClientDetails, '/api/v1/client-details/<clientId>')
api.add_resource(SPClientCases, '/api/v1/sp-client-cases/<clientId>')

# Api naming considered for the sencond time from here
api.add_resource(PeopleRegister, '/api/v1/peoples')
api.add_resource(PeopleInvitationEmail, '/api/v1/people/send-email-confirmation')
api.add_resource(PeopleDetails, '/api/v1/peoples/<id>')
api.add_resource(PeopleSetupPassword, '/api/v1/user/people/setup-password/<token>')
api.add_resource(PeopleCases, '/api/v1/people/cases/<id>/<int:page>')
api.add_resource(UpdateCommission, '/api/v1/people/change-commission/<id>')
api.add_resource(UpdateExpiryDate, '/api/v1/peoples/account-expiry/<id>')

api.add_resource(Notifications, '/api/v1/notifications')
api.add_resource(ChangeNotificationStatus, '/api/v1/notifications/<notificationId>')

api.add_resource(AddTimer, '/api/v1/timers')
api.add_resource(TotalSpentTime, '/api/v1/total-time/<caseId>')
api.add_resource(CaseTimersList, '/api/v1/case-timers/<int:page>/<caseId>')

api.add_resource(AddCustomTask, '/api/v1/tasks')
api.add_resource(CustomTasksList, '/api/v1/tasks/<int:page>')
api.add_resource(CustomTasksDetails, '/api/v1/tasks/<id>')

api.add_resource(IntakeForm, '/api/v1/intake-form')
api.add_resource(IntakeFormList, '/api/v1/intake-form/list/<int:page>')
api.add_resource(IntakeFormDetails, '/api/v1/intake/form/<id>')
api.add_resource(SendClientsIntakeForm, '/api/v1/send-intake-form/<clientId>')
api.add_resource(ShowFillUpFormForClient, '/api/v1/client-fill-form')
api.add_resource(InsertClientIntakeFormValues, '/api/v1/intake-form/filled/<formId>')
api.add_resource(ClientIntakeFormFilledDetails, '/api/v1/intake-form/filled-details/<clientId>')

api.add_resource(GoogleCredentialsDetails, '/api/v1/google-credentials-details')
api.add_resource(Authorize, '/api/v1/authorize')
api.add_resource(OAuth2CallBack, '/api/v1/oauth2callback')
api.add_resource(GoogleDriveCreateFile, '/api/v1/google-create-file')
api.add_resource(GoogleDriveFetchFiles, '/api/v1/google-fetch-files/<folder_name>')
api.add_resource(Revoke, '/api/v1/revoke')
api.add_resource(ClearCredentials, '/api/v1/clear')

api.add_resource(InitialChatMessage, '/api/v1/chat-initial-message/<room>')
api.add_resource(OldChatMessages, '/api/v1/chat-more-message/<room>')

api.add_resource(create_checkout_session, '/api/v1/create-checkout-session')
api.add_resource(create_subscription_checkout_session, '/api/v1/create-subscription-checkout-session/<type>')
api.add_resource(Webhook, '/api/v1/webhooks')
api.add_resource(Onboard_user, '/api/v1/onboard')
api.add_resource(Onboard_user_refresh, '/api/v1/onboard-user/refresh')
api.add_resource(TransferInfo, '/api/v1/transfer-info/<id>')
api.add_resource(Transfer, '/api/v1/transfer')
api.add_resource(CheckoutTransactions, '/api/v1/checkout-transactions/<int:page>')
api.add_resource(ClientCaseTransactions, '/api/v1/client-case-transactions/<caseId>')
api.add_resource(SATransactions, '/api/v1/sa-transactions/<int:page>')
api.add_resource(SACaseTransactions, '/api/v1/sa-case-transactions/<caseId>')
api.add_resource(SPTransactions, '/api/v1/sp-transactions/<int:page>')
api.add_resource(SPCaseTransactions, '/api/v1/sp-case-transactions/<caseId>')
api.add_resource(UserStripeAccInfo, '/api/v1/user/stripe-acc-info')
api.add_resource(SPStripeAccInfo, '/api/v1/sadmin/check-sp-stripe/<spId>')
