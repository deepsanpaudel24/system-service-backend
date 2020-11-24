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
_employee_setup_password_parser.add_argument('confirm-password',
                                            type=str,
                                            required=True,
                                            help="This field cannot be blank"
                                            )

_employeeRoles_parser = reqparse.RequestParser()

_employeeRoles_parser.add_argument('serviceManagement',
                                type=bool,
                                required=False
                            )
_employeeRoles_parser.add_argument('clientManagement',
                                type=bool,
                                required=False
                            )
_employeeRoles_parser.add_argument('collaborator',
                                type=bool,
                                required=False
                            )
_employeeRoles_parser.add_argument('reviewer',
                                type=bool,
                                required=False
                            )
_employeeRoles_parser.add_argument('IntakeForm',
                                type=bool,
                                required=False
                            )
_employeeRoles_parser.add_argument('CustomTask',
                                type=bool,
                                required=False
                            )
_employeeRoles_parser.add_argument('notification_title',
                                type=str,
                                required=False
                            )

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


# Registers the user with email and password
class EmployeeRegister(Resource):
    @jwt_required
    def post(self):
        createdDate = datetime.today()
        expiryDate = createdDate + timedelta(days=(1*365)) 
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
                    'logout': True,
                    'createdDate': createdDate.strftime('%Y-%m-%d'),
                    'expiryDate': user.get('expiryDate')
                })                           # insert the data in the collection users                                                                                              
                return {"message": "Employee added successfully! "}, 201
            return {"message": "You are not allowed to add employee"}, 403
        return {
            "message": "Failed to add employee"
        }, 403

class SendEmployeeEmailInvitation(Resource):
    @jwt_required
    def post(self):
        data = _employee_parser.parse_args()
        token = s.dumps(data['email'], salt='employee-email-confirm')
        link_react = "http://localhost:3000/user/employee/password-setup/{}".format(token)
        msg = Message(
            subject = "Email confirmation for Service-System",
            sender = "rukshan.shady@gmail.com",
            recipients=[data['email']],
            body="You have been invited on Service-System. Please open the link to verify setup your account. {}".format(link_react) 
        )
        mail.send(msg)


# Reset password confirmation of the user 
class EmployeeSetupPassword(Resource):
    def put(self, token):
        try:
            data = _employee_setup_password_parser.parse_args()
            setup_password_employee = s.loads(token, salt='employee-email-confirm', max_age=600)
            if setup_password_employee:
                if data['password'] == data['confirm-password']:
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
                return { "message", "Password and confirm password does not match"}, 403
        except SignatureExpired:
            return {"message": "The verification token has expired now. Please reset again."}, 401
        except BadTimeSignature:
            return {"message": "The verification token is invalid"}, 401

# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    employees = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find( 
        {"$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "email": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "name": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_number = result.count()
    for emp in result:
        main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
        total_records = main_query.count()
        emp['no_cases'] = total_records
        employees.append(emp)
    return employees, total_number

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    employees = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.users.find( 
        {"$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "email": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "name": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    # This gives the total number of results we have so that the frontend can work accordingly
    total_number = query.count()
    for emp in query:
        main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
        total_records = main_query.count()
        emp['no_cases'] = total_records
        employees.append(emp)
    return employees, total_number

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    employees = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find ( 
        { "$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) } , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_number = result.count()
    for emp in result:
        main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
        total_records = main_query.count()
        emp['no_cases'] = total_records
        employees.append(emp)
    return employees, total_number

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    employees = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find( 
        {"$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "email": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "name": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    )
    total_number = result.count()
    for emp in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
        total_records = main_query.count()
        emp['no_cases'] = total_records
        employees.append(emp)
    return employees, total_number

# FOR THE SEARCH
def Search(*args, **kwargs):
    employees = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.users.find( 
        {"$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "email": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "name": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    )
    # This gives the total number of results we have so that the frontend can work accordingly
    total_number = query.count()
    for emp in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
        total_records = main_query.count()
        emp['no_cases'] = total_records
        employees.append(emp)
    return employees, total_number

# FOR THE FILTERS
def Filter(*args, **kwargs):
    employees = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find ( { "$and": [ { 'owner': ObjectId ( kwargs.get('current_user') ) } , { "$or": query_list } ] } )
    total_number = result.count()
    for emp in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
        total_records = main_query.count()
        emp['no_cases'] = total_records
        employees.append(emp)
    return employees, total_number

# FOR THE SORTING
def Sorting(*args, **kwargs):
    employees = []
    # take the value from list 
    total_number = mongo.db.users.find ( {'owner': ObjectId ( kwargs.get('current_user') ) } ).count()
    for emp in mongo.db.users.find( {'owner': ObjectId ( kwargs.get('current_user') ) } ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
        total_records = main_query.count()
        emp['no_cases'] = total_records
        employees.append(emp)
    return employees, total_number

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    employees = []
    total_number = mongo.db.users.find ( {'owner': ObjectId ( kwargs.get('current_user') ) } ).count()
    for emp in mongo.db.users.find( {'owner': ObjectId ( kwargs.get('current_user') ) } ).sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
        total_records = main_query.count()
        emp['no_cases'] = total_records
        employees.append(emp)
    return employees, total_number

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 


class UserEmployeeList(Resource):
    @jwt_required
    def get(self, page):
        current_user = get_jwt_identity()
        table_rows = app.config['MAX_TABLE_ROWS']
        employees = []
        count = page-1
        offset = table_rows*count
        total_number = mongo.db.users.find({'owner': ObjectId(current_user)}).count()
        for emp in mongo.db.users.find({'owner': ObjectId(current_user)}).sort("_id", -1).limit(table_rows).skip(offset):
            main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(emp.get('_id')) } } } )
            total_records = main_query.count()
            emp['no_cases'] = total_records
            employees.append(emp)
        return {'employees': json.loads(json.dumps(employees, default=json_util.default)), 'total_records': total_number, 'page' : page}

    @jwt_required
    def post(self, page):
        current_user = get_jwt_identity()
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        employees = []
        count = page-1
        offset = table_rows*count
        value  = {
            "current_user": current_user,
            "table_rows": table_rows,
            "offset": offset
        }

        # for all three , search, filter and sorting
        if data.get('keyword') and len(data.get('filters')) > 0 and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandFilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'employees': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'employees': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'employees': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'employees': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'employees': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'employees': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'employees': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'employees': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}
            

# class to provide the employee details 
class EmployeeDetails(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "SPCA" or user.get('user_type') == "CCA":
            employee_details = mongo.db.users.find_one({'_id': ObjectId(id)})
            main_query = mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(id) } } } )
            total_records = main_query.count()
            employee_details['no_cases'] = total_records
            return json.loads(json.dumps(employee_details, default=json_util.default))
        return {"message" : "You are not authorized to view this page"}, 403

    @jwt_required
    def delete(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "SPCA" or user.get('user_type') == "CCA":
            employee_details = mongo.db.users.remove({'_id': ObjectId(id)})
            return {"message": "User has been removed permanently"}, 200
    
    @jwt_required
    def put(self, id):
        rolesData= _employeeRoles_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SA":
            current_employee = mongo.db.users.find_one({'_id': ObjectId(id)})
            if current_employee:
                mongo.db.users.update_one({'_id': ObjectId(id)}, {
                        '$set': {
                        'serviceManagement': rolesData['serviceManagement'],
                        'clientManagement': rolesData['clientManagement'],
                        'collaborator': rolesData['collaborator'],
                        'reviewer': rolesData['reviewer'],
                        'IntakeForm': rolesData['IntakeForm'],
                        'CustomTask': rolesData['CustomTask']
                    }
                })
                return {
                    "message": "Roles update successsfull"
                }, 200
            return {
                "message": "Employee does not exist"
            }, 404
        return {
            "message": "You are not authorized to assign roles to employee"
        }, 403

        