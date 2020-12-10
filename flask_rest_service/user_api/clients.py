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
from datetime import datetime, timedelta
import uuid
import werkzeug
from werkzeug.utils import secure_filename
from flask_rest_service.notifications import InsertNotifications


_client_parser =  reqparse.RequestParser()

_client_parser.add_argument('email',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

_client_setup_password_parser = reqparse.RequestParser()

_client_setup_password_parser.add_argument('password',
                                            type=str,
                                            required=True,
                                            help="This field cannot be blank"
                                            )
_client_setup_password_parser.add_argument('confirm-password',
                                            type=str,
                                            required=True,
                                            help="This field cannot be blank"
                                            )

_parse = reqparse.RequestParser()

_newCaseRequest_parser =  reqparse.RequestParser()

_newCaseRequest_parser.add_argument('title',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                    )
_newCaseRequest_parser.add_argument('desc',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )
_newCaseRequest_parser.add_argument('rate',
                        type=str,
                        required=False,
                        help="This field is blank."
                    )
_newCaseRequest_parser.add_argument('rateType',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )
_newCaseRequest_parser.add_argument('caseTags',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )



s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    clients = []

    if kwargs.get('user_type') == "SPCAe":
        main_condition = { 'invited_by': ObjectId(kwargs.get('owner') ) }
    else: 
        main_condition = { 'invited_by': ObjectId( kwargs.get('current_user') ) }

    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "username": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "name": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for client in result:
        clients.append(client)
    return clients, total_records

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    clients = []

    if kwargs.get('user_type') == "SPCAe":
        main_condition = { 'invited_by': ObjectId(kwargs.get('owner') ) }
    else: 
        main_condition = { 'invited_by': ObjectId( kwargs.get('current_user') ) }

    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.users.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "username": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "name": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for client in query:
        clients.append(client)
    return clients, total_records

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    clients = []

    if kwargs.get('user_type') == "SPCAe":
        main_condition = { 'invited_by': ObjectId(kwargs.get('owner') ) }
    else: 
        main_condition = { 'invited_by': ObjectId( kwargs.get('current_user') ) }

    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find ( 
        { "$and": [ 
                    main_condition , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for client in result:
        clients.append(client)
    return clients, total_records

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    clients = []
    if kwargs.get('user_type') == "SPCAe":
        main_condition = { 'invited_by': ObjectId(kwargs.get('owner') ) }
    else: 
        main_condition = { 'invited_by': ObjectId( kwargs.get('current_user') ) }

    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "username": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "name": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    )
    total_records = result.count()
    for client in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        clients.append(client)
    return clients, total_records

# FOR THE SEARCH
def Search(*args, **kwargs):
    clients = []
    if kwargs.get('user_type') == "SPCAe":
        main_condition = { 'invited_by': ObjectId(kwargs.get('owner') ) }
    else: 
        main_condition = { 'invited_by': ObjectId( kwargs.get('current_user') ) }

    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.users.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "username": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "name": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    )
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for client in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        clients.append(client)
    return clients, total_records

# FOR THE FILTERS
def Filter(*args, **kwargs):
    clients = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    
    if kwargs.get('user_type') == "SPCAe":
        main_condition = { 'invited_by': ObjectId(kwargs.get('owner') ) }
    else: 
        main_condition = { 'invited_by': ObjectId( kwargs.get('current_user') ) }

    result = mongo.db.users.find ( { "$and": [ main_condition , { "$or": query_list } ] } )
    total_records = result.count()
    for client in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        clients.append(client)
    return clients, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    clients = []
    # take the value from list 
    if kwargs.get('user_type') == "SPCAe":
        main_query = mongo.db.users.find( { 'invited_by': ObjectId(kwargs.get('owner') ) } )
    else: 
        main_query = mongo.db.users.find( { 'invited_by': ObjectId( kwargs.get('current_user') ) } )

    total_records = main_query.count()
    for client in main_query.sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        clients.append(client)
    return clients, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    clients = []

    if kwargs.get('user_type') == "SPCAe":
        main_query = mongo.db.users.find( { 'invited_by': ObjectId(kwargs.get('owner')) } )
    else: 
        main_query = mongo.db.users.find( { 'invited_by': ObjectId( kwargs.get('current_user') ) } )

    total_records = main_query.count()
    for client in main_query.sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        clients.append(client)
    return clients, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 


class UserClientList(Resource):
    @jwt_required
    def get(self, page):
        current_user = get_jwt_identity()
        user_details = mongo.db.users.find_one( { '_id': ObjectId(current_user) } )
        table_rows = app.config['MAX_TABLE_ROWS']
        clients = []
        count = page-1
        offset = table_rows*count
        
        if user_details.get('user_type') == "SPCAe":
            main_query = mongo.db.users.find( { 'invited_by': ObjectId(user_details.get('owner')) } )
        else: 
            main_query = mongo.db.users.find( { 'invited_by': ObjectId(current_user) } )
        
        total_records = main_query.count()
        for client in main_query.sort("_id", -1).limit(table_rows).skip(offset):
            clients.append(client)
        return {'clients': json.loads(json.dumps(clients, default=json_util.default)), 'total_records': total_records, 'page' : page}

    @jwt_required
    def post(self, page):
        current_user = get_jwt_identity()
        user_details = mongo.db.users.find_one( { '_id': ObjectId(current_user) } )
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        services = []
        count = page-1
        offset = table_rows*count
        value  = {
            "current_user": current_user,
            "table_rows": table_rows,
            "offset": offset,
            "user_type": user_details.get('user_type'),
            "owner": user_details.get('owner')
        }

        # for all three , search, filter and sorting
        if data.get('keyword') and len(data.get('filters')) > 0 and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandFilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'clients': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'clients': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'clients': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'clients': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'clients': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'clients': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'clients': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'clients': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}




# Registers the user with email and password
class ClientRegister(Resource):
    @jwt_required
    def post(self):
        createdDate = datetime.today()
        expiryDate = createdDate + timedelta(days=(1*7)) 
        data = _client_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            if user.get("user_type") == "SPCA" or user.get("user_type") == "SPS":
                client_existence = mongo.db.users.find_one({'email': data['email']})
                if client_existence:
                    return {"message": "Email already registered in the system"}, 400
                username = data['email'].split('@')[0]
                id = mongo.db.users.insert({
                    'email': data['email'],
                    'username': username,
                    'password':'',
                    'user_type':"CCA",
                    'is_verified': False,
                    'invited_by': ObjectId(current_user),
                    'profile_basic_completion': False,
                    'profile_detailed_completion': False,
                    'profile_billing_completion': True,
                    'commission': "5",
                    'logout': True,
                    'createdDate': createdDate.strftime('%Y-%m-%d'),
                    'expiryDate': expiryDate.strftime('%Y-%m-%d')
                })                           # insert the data in the collection users                                                                                              
                return {"message": "Client added successfully! "}, 201
            elif user.get("user_type") == "SPCAe":
                client_existence = mongo.db.users.find_one({'email': data['email']})
                if client_existence:
                    return {"message": "Email already registered in the system"}, 400
                id = mongo.db.users.insert({
                    'email': data['email'],
                    'password':'',
                    'user_type':"CCA",
                    'is_verified': False,
                    'invited_by': ObjectId(user.get("owner")),
                    'profile_basic_completion': False,
                    'profile_detailed_completion': False,
                    'profile_billing_completion': True,
                    'logout': True,
                    'createdDate': createdDate.strftime('%Y-%m-%d'),
                    'expiryDate': expiryDate.strftime('%Y-%m-%d')
                })                           # insert the data in the collection users                                                                                              
                return {"message": "Client added successfully! "}, 201
            return {"message": "You are not allowed to add client"}, 403
        return {
            "message": "Failed to add client"
        }, 403

class ClientEmailConfrimation(Resource):
    def post(self):
        data = _client_parser.parse_args()
        token = s.dumps(data['email'], salt='client-email-confirm')
        link_react = "http://localhost:3000/user/client/password-setup/{}".format(token)
        msg = Message(
            subject = "Email confirmation for Service-System",
            sender = "rukshan.shady@gmail.com",
            recipients=[data['email']],
            body="You have been invited on Service-System. Please open the link to verify and setup your account. {}".format(link_react) 
        )
        mail.send(msg)

# Reset password confirmation of the user 
class ClientSetupPassword(Resource):
    def put(self, token):
        try:
            data = _client_setup_password_parser.parse_args()
            setup_password_client = s.loads(token, salt='client-email-confirm', max_age=600)
            if setup_password_client:
                if data['password'] == data['confirm-password']:
                    user = mongo.db.users.find_one({'email': setup_password_client})
                    _hased_password = generate_password_hash(data['password'])      # Password hasing
                    if user:
                        mongo.db.users.update_one({'email': setup_password_client}, {
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
                return { "message": "Password and confirm-password does not match"}
        except SignatureExpired:
            return {"message": "The verification token has expired now. Please reset again."}, 401
        except BadTimeSignature:
            return {"message": "The verification token is invalid"}, 401


class ClientDetails(Resource):
    @jwt_required
    def get(self, clientId):
        current_user = get_jwt_identity()
        client_details = mongo.db.users.find_one({'_id': ObjectId(clientId)})
        return json.loads(json.dumps(client_details, default=json_util.default))
    

class SendClientsIntakeForm(Resource):
    @jwt_required
    def put(self, clientId):
        current_user = get_jwt_identity()
        data = request.get_json()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        assigned_form_list = list(map(lambda x: ObjectId(x), data['forms_id']))
        if user:
            mongo.db.users.update_one({'_id': ObjectId(clientId)}, {
                    '$set': {
                    'intake_forms': assigned_form_list,        
                }
            })      
          
            return {"message": "Form sent successfully!"}, 200
        return {
            "message": "User does not exist"
        }, 400


class ShowFillUpFormForClient(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if 'intake_forms' in user:
            last_form = user['intake_forms'][-1]
            result = mongo.db.intake_form_values.find_one({'formId': ObjectId(last_form)})
            if result:
                return { "message": "Form already filled"}
            form = mongo.db.intake_forms.find_one({'_id': ObjectId(last_form)})
            return json.loads(json.dumps(form, default=json_util.default))
        return {"message" : "No form has been assigned.."}, 404

class InsertClientIntakeFormValues(Resource):
    @jwt_required
    def post(self, formId):
        data = request.get_json()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        form_details = mongo.db.intake_forms.find_one({'_id': ObjectId(formId)})
        if user:
            id = mongo.db.intake_form_values.insert({
                'formId': ObjectId(formId),
                'formValues':data['formValues'],
                'filledBy': ObjectId(current_user),
                'filledDate': datetime.today().strftime('%Y-%m-%d')
            })                           # insert the data in the collection intake_form_values      
            # Send notifiations to the service provider saying they received the filled up client intake form. 
            notification_values = {
                "title" : f"{user.get('name')} has filled up the form you requested",
                "sender": ObjectId(current_user),
                "receiver": form_details.get('createdBy'),
                "link": f"/user/client/{current_user}"
            } 
            InsertNotifications(**notification_values)                                                                                          
            return {"message": "Form filled successfully! "}, 201
        return {
            "message": "User does not exist"
        }, 403

class ClientIntakeFormFilledDetails(Resource):
    @jwt_required
    def get(self, clientId):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        client = mongo.db.users.find_one({'_id': ObjectId(clientId)})
        # Step 1: Find which Intake form current user sent to this client
        if 'intake_forms' in client:
            form_list = list(map(lambda x: str(x), client['intake_forms']))
            #form_list = client['intake_forms']
            # Check if the client has filled the form with that id
            form_filled = []
            for form_id in form_list:
                result = mongo.db.intake_form_values.find_one({'formId': ObjectId(form_id)})
                form_details = mongo.db.intake_forms.find_one({'_id': ObjectId(form_id)})
                if result:
                    result['form_title'] = form_details.get('title')
                    form_filled.append(result)
            if form_filled:
                return json.loads(json.dumps(form_filled, default=json_util.default))
            else:
                return { "message": "Client has not filled the form"}
        return{"message": "No intake form has been sent to the client"}


# For the list of the cases that services provider gets to see 
# In the client details page, in service provider dashboard 
# Client Management module
class SPClientCases(Resource):
    @jwt_required
    def get(self, clientId):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS" or user.get('user_type') == "SPCAe":
            cases = []
            for case in mongo.db.cases.find({"$and": [{"client": ObjectId(clientId)}, {"serviceProvider": ObjectId(current_user)}]}).sort("_id", -1):
                cases.append(case)
            return json.loads(json.dumps(cases, default=json_util.default))
        return {
            "message": "You are not authorized to view cases for this client"
        }, 403 

# To create the case manually for the client by the service provider
# Client and Case Management Module
class CreateClientCase(Resource):
    @jwt_required
    def post(self, clientId):
        current_user = get_jwt_identity()
        data = _newCaseRequest_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        client = mongo.db.users.find_one({'_id': ObjectId(clientId)})
        if user.get('user_type') == "CCA" or user.get('user_type') == "CS":
            userType = "c"
        else:
            userType = "sp"

        assigned_emp_list  = {}
        # Incase if the employee is adding the case manually on behalf of admin
        if user.get('user_type') == "SPCAe":
            current_user = user.get('owner')
            assigned_emp_list = [ObjectId(get_jwt_identity())]

        caseTags = data['caseTags'].split(',')

        myFiles = request.files
        for key in myFiles:
            _parse.add_argument(
                key, type=werkzeug.datastructures.FileStorage, location='files')
        args = _parse.parse_args()
        filesLocationList = []
        for key in myFiles:
            file = args[key]
            filename = secure_filename(file.filename)
            filename, extension = filename.split('.')
            filename = f"{filename}-{uuid.uuid4().hex}.{userType}.{extension}"
            dirToSaveFile = '/'.join(app.config['UPLOAD_FOLDER'].split('/')[1:])
            filesLocationList.append(f"{dirToSaveFile}/{filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        id = mongo.db.cases.insert({
            'title': data['title'],
            'desc': data['desc'],
            'rateType': data['rateType'],
            'rate': data['rate'],
            'caseTags': caseTags,
            'status': "Contract-Waiting",
            'serviceProvider': ObjectId(current_user),
            'serviceProvidername': user.get('name'),
            'client': ObjectId(clientId),
            'clientName': client.get('name'),
            'files': filesLocationList,
            'type': "manual",
            'assigned_employee_list': assigned_emp_list,
            'requestedDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection cases    

        # Send notifiations to the client saying the service provider added a case on behalf of them
        notification_values = {
            "title" : f"{user.get('name')} has added a case for you.",
            "sender": ObjectId(current_user),
            "receiver": ObjectId(clientId),
            "link": "/user/cases"
        } 
        InsertNotifications(**notification_values)                                                 
        return {"message": "Case requested successfully! "}, 201
