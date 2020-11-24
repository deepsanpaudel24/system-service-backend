from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime


_newServiceRegister_parser =  reqparse.RequestParser()

_newServiceRegister_parser.add_argument('title',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_newServiceRegister_parser.add_argument('rateType',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_newServiceRegister_parser.add_argument('rate',
                    type=float,
                    required=False,
                    help="This field cannot be blank."
                    )
_newServiceRegister_parser.add_argument('averageTimeTake',
                    type=float,
                    required=False,
                    help="This field cannot be blank."
                    )


# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    services = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.services.find( 
        {"$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "rate": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "averageTimeTaken": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for service in result:
        services.append(service)
    return services, total_records

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    services = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.services.find( 
        {"$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "rate": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "averageTimeTaken": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for service in query:
        services.append(service)
    return services, total_records

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    services = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.services.find ( 
        { "$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) } , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for service in result:
        services.append(service)
    return services, total_records

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    services = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.services.find( 
        {"$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "rate": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "averageTimeTaken": { "$regex": f".*{kwargs.get('search_keyword')}.*" } }  
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    )
    total_records = result.count()
    for service in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        services.append(service)
    return services, total_records

# FOR THE SEARCH
def Search(*args, **kwargs):
    services = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.services.find( 
        {"$and": [ 
                    { 'owner': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "rate": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "averageTimeTaken": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    )
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for service in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        services.append(service)
    return services, total_records

# FOR THE FILTERS
def Filter(*args, **kwargs):
    services = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.services.find ( { "$and": [ { 'owner': ObjectId ( kwargs.get('current_user') ) } , { "$or": query_list } ] } )
    total_records = result.count()
    for service in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        services.append(service)
    return services, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    services = []
    # take the value from list 
    total_records = mongo.db.services.find ( {'owner': ObjectId ( kwargs.get('current_user') ) } ).count()
    for service in mongo.db.services.find( {'owner': ObjectId ( kwargs.get('current_user') ) } ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        services.append(service)
    return services, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    services = []
    total_records = mongo.db.services.find ( {'owner': ObjectId ( kwargs.get('current_user') ) } ).count()
    for service in mongo.db.services.find( {'owner': ObjectId ( kwargs.get('current_user') ) } ).sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        services.append(service)
    return services, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

class ServicesList(Resource):
    @jwt_required
    def get(self, page):
        current_user = get_jwt_identity()
        table_rows = app.config['MAX_TABLE_ROWS']
        services = []
        count = page-1
        offset = table_rows*count
        total_records = mongo.db.services.find({'owner': ObjectId(current_user)}).count()
        for service in mongo.db.services.find({'owner': ObjectId(current_user)}).sort("_id", -1).limit(table_rows).skip(offset):
            services.append(service)
        return {'services': json.loads(json.dumps(services, default=json_util.default)), 'total_records': total_records, 'page' : page}

    @jwt_required
    def post(self, page):
        current_user = get_jwt_identity()
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        services = []
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
            return {'services': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'services': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'services': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'services': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'services': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'services': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'services': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'services': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}

class SaViewServicesList(Resource):
    @jwt_required
    def get(self, ownerid):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "SAe":
            services = []
            for service in mongo.db.services.find({'owner': ObjectId(ownerid)}).sort("_id", -1):
                services.append(service)
            return json.loads(json.dumps(services, default=json_util.default))
        return {
            "message": "You are not authorized to view cases"
        }, 403 

class Service(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = _newServiceRegister_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        id = mongo.db.services.insert({
            'title': data['title'],
            'rateType': data['rateType'],
            'rate': data['rate'],
            'averageTimeTaken': data['averageTimeTake'],
            'owner': ObjectId(current_user),
            'status': "Active",
            'createdDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection cases                                                                                            
        return {"message": "Service added successfully! "}, 201

class ServiceAction(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPCAe" or user.get('user_type') == "SPS":
            service_details = mongo.db.services.find_one({'_id': ObjectId(id)})
            return json.loads(json.dumps(service_details, default=json_util.default))
        return {"message" : "You are not authorized to view this page"}, 403

    @jwt_required
    def put(self, id):
        data= _newServiceRegister_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPCAe" or user.get('user_type') == "SPS":
            mongo.db.services.update_one({'_id': ObjectId(id)}, {
                        '$set': {
                        'title': data['title'],
                        'rateType': data['rateType'],
                        'rate': data['rate'],
                        'averageTimeTaken': data['averageTimeTake']
                    }
                })
            return {
                "message": "Service updated sucessfully"
            }, 200

    @jwt_required
    def delete(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPCAe" or user.get('user_type') == "SPS":
            service_details = mongo.db.services.remove({'_id': ObjectId(id)})
            return {"message": "Service has been removed permanently"}, 200