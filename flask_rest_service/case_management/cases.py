from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
from bson import json_util
from flask_rest_service.notifications import InsertNotifications

_forwardTo_parser = reqparse.RequestParser()

_forwardTo_parser.add_argument('service_providers',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )

# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    cases = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.cases.find( 
        {"$and": [ 
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
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.cases.find(  
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "status": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "requestedDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } }  
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
    result = mongo.db.cases.find (  
                    { "$or": query_list }
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
    result = mongo.db.cases.find( 
        {"$and": [  
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
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.cases.find( 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "status": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "requestedDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
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
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.cases.find ( { "$or": query_list } )
    total_records = result.count()
    for case in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        cases.append(case)
    return cases, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    cases = []
    # take the value from list 
    total_records = mongo.db.cases.find ( ).count()
    for case in mongo.db.cases.find().sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        cases.append(case)
    return cases, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    cases = []
    total_records = mongo.db.cases.find ( ).count()
    for case in mongo.db.cases.find( ).sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        cases.append(case)
    return cases, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

class Cases(Resource):
    @jwt_required
    def get(self, page):
        current_user = get_jwt_identity()
        table_rows = app.config['MAX_TABLE_ROWS']
        cases = []
        count = page-1
        offset = table_rows*count
        total_records = mongo.db.cases.find().count()
        for case in mongo.db.cases.find().sort("_id", -1).limit(table_rows).skip(offset):
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



# class ClientCases(Resource):
#     @jwt_required
#     def get(self):
#         current_user = get_jwt_identity()
#         user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
#         if user.get('user_type') == "CCA" or user.get('user_type') == "CS":
#             cases = []
#             for case in mongo.db.cases.find({'client': ObjectId(current_user)}).sort("_id", -1):
#                 cases.append(case)
#             return json.loads(json.dumps(cases, default=json_util.default))
#         return {
#             "message": "You are not authorized to view cases"
#         }, 403 

class ServiceProviderCases(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS" or user.get('user_type') == "SPCAe":
            cases = []
            
            # Condition 1: forwardTo has current_user in case if case status != On-progress or completed 
            # Condition 2: serviceProvider has current_user

            # condition to check if the user is listed in the forwardTo
            condition_one = {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(current_user) } } }
            # condition to check if the case that has the current user listed in the forwardTo has not been to progress
            # This is because the cases that are in progress cannot be seen by other service providers
            condition_two = {"$or" : [{"status": {"$ne": "On-progress"}}, {"status": {"$ne": "Completed"}}]}

            for case in mongo.db.cases.find({"$or": [{"$and": [condition_one, condition_two]}, {"serviceProvider": ObjectId(current_user)}]}).sort("_id", -1):
                cases.append(case)
            return json.loads(json.dumps(cases, default=json_util.default))
        return {
            "message": "You are not authorized to view cases"
        }, 403

# class EmployeeCases(Resource):
#     @jwt_required
#     def get(self):
#         current_user = get_jwt_identity()
#         user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
#         if user.get('user_type') == "SPCAe" or user.get('user_type') == "CCAe":
#             cases = []
#             for case in mongo.db.cases.find( {"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(current_user) } } } ).sort("_id", -1):
#                 cases.append(case)
#             return json.loads(json.dumps(cases, default=json_util.default))
#         return {
#             "message": "You are not authorized to view cases"
#         }, 403

class ServiceProviderCasesActive(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        cases = []
        for case in mongo.db.cases.find({"$and": [{"status": "On-progress"}, {"serviceProvider": ObjectId(current_user)}]}).sort("_id", -1):
            cases.append(case)
        return json.loads(json.dumps(cases, default=json_util.default))
        

# this case details can be viewed either by the SA or the respective client 
# or if the SP and its employee are assigned 
class ClientCasesDetails(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "CCA" or user.get('user_type') == "CS":
            case_details = mongo.db.cases.find_one({'_id': ObjectId(id)})
            case_details['logged_in_user_name'] = user.get('name')
            case_details['logged_in_user_id'] = user.get('_id')
            result  = list(mongo.db.users.find(
                { "service_categories": { "$elemMatch": { "$in": case_details.get('caseTags') } } }
                ))
            for service_provider in result:
                main_query = mongo.db.cases.find( {"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(service_provider.get('_id')) } } } )
                total_records = main_query.count()
                service_provider['no_forwarded_cases'] = total_records
            for service_provider in result:
                main_query = mongo.db.cases.find( { "$and": [ {'serviceProvider': ObjectId(service_provider.get('_id'))} , {"status": "On-progress"} ] } )
                total_records = main_query.count()
                service_provider['no_progress_cases'] = total_records
            forwardedSP_list = []
            if "forwardTo" in case_details:
                forwardedSP_list = mongo.db.users.find({
                    "_id" : { "$in": case_details.get('forwardTo') }
                })
            response = {
                "case_details": case_details,
                "matchingServiceProviders": result,
                "forwardedSP_list": forwardedSP_list
            }

            return json.loads(dumps(response))
        return {"message" : "You are not authorized to view this page"}, 403



class ServiceProviderCasesDetails(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS" or user.get('user_type') == "SPCAe":
            case_details = mongo.db.cases.find_one({'_id': ObjectId(id)})
            client = mongo.db.users.find_one({'_id': ObjectId(case_details.get('client'))})
            case_details['intro_video'] = client.get('intro_video')
            case_details['intro_text'] = client.get('intro_text')
            case_details['logged_in_user_name'] = user.get('name')
            case_details['logged_in_user_id'] = user.get('_id')
            return json.loads(json.dumps(case_details, default=json_util.default))
        return {"message" : "You are not authorized to view this page"}, 403

class ForwardCaseRequest(Resource):
    @jwt_required
    def put(self, id):
        current_user = get_jwt_identity()
        forwardData= _forwardTo_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA":
            serviceProviders = forwardData['service_providers'].split(',')
            serviceProviders = list(map(lambda x: ObjectId(x), serviceProviders))
            mongo.db.cases.update_one({'_id': ObjectId(id)}, {
                    '$set': {
                    'forwardTo': serviceProviders,
                    'status': "Forwarded"
                }
            })
            # Send notifiations to the service providers with the message saying they received the case from super admin. 
            for serviceProvider in serviceProviders:
                notification_values = {
                    "title" : "A case forwarded by super-admin has been received",
                    "sender": ObjectId(current_user),
                    "receiver": serviceProvider,
                    "link": f"/user/case/{id}"
                } 
                InsertNotifications(**notification_values)

            return {"message": "Case forwarded to all the service providers"}, 200
        return {
            "user_type": str(user.get('user_type'))
        }, 403


class UndoCaseForward(Resource):
    @jwt_required
    def put(self, id):
        data = request.get_json()
        mongo.db.cases.update_one( { "_id": ObjectId(id) }, { "$pull": { "forwardTo": ObjectId(data.get('service_providers')) } } )
        # forwardData= _forwardTo_parser.parse_args()
        # serviceProviders = forwardData['service_providers'].split(',')
        # print("service providers list", serviceProviders)
        # serviceProviders = list(map(lambda x: ObjectId(x), serviceProviders))
        # mongo.db.cases.update_one({'_id': ObjectId(id)}, {
        #             '$set': {
        #             'forwardTo': serviceProviders,
        #             'status': "Forwarded"
        #         }
        #     })
        return {"message": "Case forward was retrieved"}


class RequestCaseCompletion(Resource):
    @jwt_required
    def put(self, id):
        data = request.get_json()
        current_user = get_jwt_identity()
        case_details = mongo.db.cases.find( { '_id': ObjectId(id) } )
        mongo.db.cases.update_one({'_id': ObjectId(id)}, {
                    '$set': {
                    'status': "Request-Completion"
                }
            })
        notification_values = {
            "title" : "A case forwarded by super-admin has been received",
            "sender": ObjectId(current_user),
            "receiver": ObjectId(case_details.get('client')),
            "link": f"/user/case/{id}"
        } 
        InsertNotifications(**notification_values)
        return { "message" : "Completion request made sucessfully" }, 200

class ConfirmCaseCompletion(Resource):
    @jwt_required
    def put(self, id):
        data = request.get_json()
        mongo.db.cases.update_one({'_id': ObjectId(id)}, {
                    '$set': {
                    'status': "Confirm-Completion"
                }
            })
        return { "message" : "Completion confirmed sucessfully" }, 200

            