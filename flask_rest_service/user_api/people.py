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

_people_setup_password_parser = reqparse.RequestParser()

_people_setup_password_parser.add_argument('password',
                                            type=str,
                                            required=True,
                                            help="This field cannot be blank"
                                            )
_people_setup_password_parser.add_argument('confirm-password',
                                            type=str,
                                            required=True,
                                            help="This field cannot be blank"
                                            )

s = URLSafeTimedSerializer('secret_key')    # Serizer instance with the secret key. This key should be kept secret.


# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    peoples = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find( 
        {"$and": [ 
                    { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } }, 
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
    total_records = result.count()
    for people in result:
        peoples.append(people)
    return peoples, total_records

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    peoples = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.users.find( 
        {"$and": [ 
                    { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } }, 
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
    total_records = query.count()
    for people in query:
        peoples.append(people)
    return peoples, total_records

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    peoples = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find ( 
        { "$and": [ 
                    { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for people in result:
        peoples.append(people)
    return peoples, total_records

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    peoples = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find( 
        {"$and": [ 
                    { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } }, 
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
    total_records = result.count()
    for people in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        peoples.append(people)
    return peoples, total_records

# FOR THE SEARCH
def Search(*args, **kwargs):
    peoples = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    
    query = mongo.db.users.find( 
        {"$and": [ 
                    { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } }, 
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
    total_records = query.count()
    for people in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        peoples.append(people)
    return peoples, total_records

# FOR THE FILTERS
def Filter(*args, **kwargs):
    peoples = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.users.find ( { "$and": [ { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } , { "$or": query_list } ] } )
    total_records = result.count()
    for people in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        peoples.append(people)
    return peoples, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    peoples = []
    # take the value from list 
    total_records = mongo.db.users.find ( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).count()
    for people in mongo.db.users.find( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        peoples.append(people)
    return peoples, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    peoples = []
    total_records = mongo.db.users.find ( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).count()
    for people in mongo.db.users.find( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        peoples.append(people)
    return peoples, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

class PeopleList(Resource):
    @jwt_required
    def get(self, page):
        current_user = get_jwt_identity()
        table_rows = app.config['MAX_TABLE_ROWS']
        peoples = []
        count = page-1
        offset = table_rows*count
        total_records = mongo.db.users.find( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).count()
        for people in mongo.db.users.find( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).sort("_id", -1).limit(table_rows).skip(offset):
            peoples.append(people)
        return {'peoples': json.loads(json.dumps(peoples, default=json_util.default)), 'total_records': total_records, 'page' : page}

    @jwt_required
    def post(self, page):
        current_user = get_jwt_identity()
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        peoples = []
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
            return {'peoples': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'peoples': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'peoples': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'peoples': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'peoples': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'peoples': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'peoples': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'peoples': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}


class PeopleRegister(Resource):
    @jwt_required
    def post(self):
        createdDate = datetime.today()
        expiryDate = createdDate + timedelta(days=(1*7))
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
                    'createdDate': createdDate.strftime('%Y-%m-%d'),
                    'expiryDate': expiryDate.strftime('%Y-%m-%d')
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
        for people in mongo.db.users.find( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).sort("_id", -1):
            peoples.append(people)
        return json.loads(json.dumps(peoples, default=json_util.default))


class PeopleInvitationEmail(Resource):
    def post(self):
        data = _people_parser.parse_args()
        token = s.dumps(data['email'], salt='people-email-confirm')
        link_react = "http://localhost:3000/user/people/password-setup/{}".format(token)
        msg = Message(
            subject = "Email confirmation for Service-System",
            sender ="rukshan.shady@gmail.com",
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
            employees = mongo.db.users.find ( {'owner': ObjectId(id) } ).count()
            if employees > 0:
                for user in mongo.db.users.find({'owner': ObjectId(id)}):
                    mongo.db.users.update_one({'owner': ObjectId(id)}, {
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


# Setup password confirmation of the peoples invited by the Superadmin 
class PeopleSetupPassword(Resource):
    def put(self, token):
        try:
            data = _people_setup_password_parser.parse_args()
            setup_password_people = s.loads(token, salt='people-email-confirm', max_age=600)
            if setup_password_people:
                if data['password'] == data['confirm-password']:
                    user = mongo.db.users.find_one({'email': setup_password_people})
                    _hased_password = generate_password_hash(data['password'])      # Password hasing
                    if user:
                        mongo.db.users.update_one({'email': setup_password_people}, {
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
            return {"message": "The verification token has expired."}, 401
        except BadTimeSignature:
            return {"message": "The verification token is invalid"}, 401




class UpdateCommission(Resource):
    @jwt_required
    def put(self, id):
        data= request.get_json()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "SAe":
            mongo.db.users.update_one({'_id': ObjectId(id)}, {
                    '$set': {
                    "commission": data['commission']
                    }
                })
            return {"message": "Commission rate upated sucessfully"}, 200
        return {
            "message": "User does not exist"
        }, 400

class UpdateExpiryDate(Resource):
    @jwt_required
    def put(self, id):
        data= request.get_json()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "SAe":
            mongo.db.users.update_one({'_id': ObjectId(id)}, {
                    '$set': {
                    "expiryDate": data['expiry_date']
                    }
                })
            return {"message": "Expiry date upated sucessfully"}, 200
        return {
            "message": "User does not exist"
        }, 400

