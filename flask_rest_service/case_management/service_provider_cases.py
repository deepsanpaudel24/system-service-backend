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

# Function to check if the user and its employee has fowarded the proposal to any specific case

# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    cases = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
    # Condition 2: serviceProvider has current_user

    # condition to check if the user is listed in the forwardTo
    condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(kwargs.get('current_user')) } } }
    # condition to check if the case that has the current user listed in the forwardTo has not been to progress
    # This is because the cases that are in progress cannot be seen by other service providers
    condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
    main_condition = { "$or": [ {'client': ObjectId(kwargs.get('current_user'))}, {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(kwargs.get('current_user'))}]} ] } 

    result = mongo.db.cases.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "status": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "requestedDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for case in result:
        cases.append(case)
    return cases, total_records

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    cases = []
    # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
    # Condition 2: serviceProvider has current_user

    # condition to check if the user is listed in the forwardTo
    condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(kwargs.get('current_user')) } } }
    # condition to check if the case that has the current user listed in the forwardTo has not been to progress
    # This is because the cases that are in progress cannot be seen by other service providers
    condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
    main_condition = { "$or": [ {'client': ObjectId(kwargs.get('current_user'))}, {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(kwargs.get('current_user'))}]} ] }
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.cases.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "status": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "requestedDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for case in query:
        cases.append(case)
    return cases, total_records

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    cases = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)

    # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
    # Condition 2: serviceProvider has current_user

    # condition to check if the user is listed in the forwardTo
    condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(kwargs.get('current_user')) } } }
    # condition to check if the case that has the current user listed in the forwardTo has not been to progress
    # This is because the cases that are in progress cannot be seen by other service providers
    condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
    main_condition = { "$or": [ {'client': ObjectId(kwargs.get('current_user'))}, {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(kwargs.get('current_user'))}]} ] }

    result = mongo.db.cases.find ( 
        { "$and": [ 
                    main_condition , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for case in result:
        cases.append(case)
    return cases, total_records

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    cases = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
    # Condition 2: serviceProvider has current_user

    # condition to check if the user is listed in the forwardTo
    condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(kwargs.get('current_user')) } } }
    # condition to check if the case that has the current user listed in the forwardTo has not been to progress
    # This is because the cases that are in progress cannot be seen by other service providers
    condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
    main_condition = { "$or": [ {'client': ObjectId(kwargs.get('current_user'))}, {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(kwargs.get('current_user'))}]} ] }
    
    result = mongo.db.cases.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "status": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "requestedDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    )
    total_records = result.count()
    for case in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        cases.append(case)
    return cases, total_records

# FOR THE SEARCH
def Search(*args, **kwargs):
    cases = []
    # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
    # Condition 2: serviceProvider has current_user
    # condition to check if the user is listed in the forwardTo
    condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(kwargs.get('current_user')) } } }
    # condition to check if the case that has the current user listed in the forwardTo has not been to progress
    # This is because the cases that are in progress cannot be seen by other service providers
    condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
    main_condition = { "$or": [ {'client': ObjectId(kwargs.get('current_user'))}, {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(kwargs.get('current_user'))}]} ] }
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.cases.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "status": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "requestedDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    )
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for case in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        cases.append(case)
    return cases, total_records

# FOR THE FILTERS
def Filter(*args, **kwargs):
    cases = []
    # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
    # Condition 2: serviceProvider has current_user

    # condition to check if the user is listed in the forwardTo
    condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(kwargs.get('current_user')) } } }
    # condition to check if the case that has the current user listed in the forwardTo has not been to progress
    # This is because the cases that are in progress cannot be seen by other service providers
    condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
    main_condition = { "$or": [ {'client': ObjectId(kwargs.get('current_user'))}, {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(kwargs.get('current_user'))}]} ] }
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.cases.find ( { "$and": [ main_condition , { "$or": query_list } ] } )
    total_records = result.count()
    for case in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        cases.append(case)
    return cases, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    cases = []
    # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
    # Condition 2: serviceProvider has current_user

    # condition to check if the user is listed in the forwardTo
    condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(kwargs.get('current_user')) } } }
    # condition to check if the case that has the current user listed in the forwardTo has not been to progress
    # This is because the cases that are in progress cannot be seen by other service providers
    condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
    main_condition = { "$or": [ {'client': ObjectId(kwargs.get('current_user'))}, {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(kwargs.get('current_user'))}]} ] }
    # take the value from list 
    total_records = mongo.db.cases.find ( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).count()
    for case in mongo.db.cases.find( { "user_type": { "$nin": ["SA", "SAe", "SPCAe", "CCAe"] } } ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        cases.append(case)
    return cases, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    cases = []
    # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
    # Condition 2: serviceProvider has current_user

    # condition to check if the user is listed in the forwardTo
    condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(kwargs.get('current_user')) } } }
    # condition to check if the case that has the current user listed in the forwardTo has not been to progress
    # This is because the cases that are in progress cannot be seen by other service providers
    condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
    main_query = mongo.db.cases.find( { "$or": [ {'client': ObjectId(kwargs.get('current_user'))}, {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(kwargs.get('current_user'))}]} ] } )
    total_records = main_query.count()
    for case in main_query.sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        cases.append(case)
    return cases, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 


# For all the peoples cases in super admin dashboard
class ServiceProviderCases(Resource):
    @jwt_required
    def get(self, page):
        current_user = get_jwt_identity()
        table_rows = app.config['MAX_TABLE_ROWS']
        cases = []
        count = page-1
        offset = table_rows*count
        # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
        # Condition 2: serviceProvider has current_user

        # condition to check if the user is listed in the forwardTo
        condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(current_user) } } }
        # condition to check if the case that has the current user listed in the forwardTo has not been to progress
        # This is because the cases that are in progress cannot be seen by other service providers
        # condition_two = { "status": 
        #                         { "$nin" : [
        #                                 "On-progress",
        #                                 "Awaiting-Advance-Payment",
        #                                 "Closed"
        #                             ] 
        #                         } 
        #                 }
        condition_two = { "$or" : [ 
                                    {"status": "Requested" },
                                    {"status": "Forwarded" },
                                    {"status": "Proposal-Forwarded" }, 
                                ] 
                        }
        main_query = mongo.db.cases.find( {"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(current_user)}]} )

        total_records = main_query.count()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        for case in main_query.sort("_id", -1).limit(table_rows).skip(offset):
            # check if the case has status Proposal-Forwarded, then check if the current user has proposal forwareded to the client.
            if case.get('status') == "Proposal-Forwarded":
                if user.get('user_type') == "SPCAe":
                    proposal = mongo.db.proposals.find_one({'caseId': ObjectId(case.get('_id')), 'serviceProvider': ObjectId(user.get('owner'))})
                else:
                    proposal = mongo.db.proposals.find_one({'caseId': ObjectId(case.get('_id')), 'serviceProvider': ObjectId(current_user)})
                if proposal:
                    case['status'] = "Proposal-Forwarded"
                else:
                    case['status'] = "Forwarded"
            cases.append(case)
        return {'cases': json.loads(json.dumps(cases, default=json_util.default)), 'total_records': total_records, 'page' : page}

    @jwt_required
    def post(self, page):
        current_user = get_jwt_identity()
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        cases = []
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
            return {'cases': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'cases': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'cases': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'cases': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'cases': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'cases': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'cases': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'cases': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}