from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime


_addCustomTasks_parser =  reqparse.RequestParser()

_addCustomTasks_parser.add_argument('title',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                    )
_addCustomTasks_parser.add_argument('desc',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )
_addCustomTasks_parser.add_argument('deadline',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )



# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    tasks = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.custom_tasks.find( 
        {"$and": [ 
                    { 'workBy': ObjectId ( kwargs.get('current_user') ) }, 
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
    for task in result:
        tasks.append(task)
    return tasks, total_records

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    tasks = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.custom_tasks.find( 
        {"$and": [ 
                    { 'workBy': ObjectId ( kwargs.get('current_user') ) }, 
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
    for task in query:
        tasks.append(task)
    return tasks, total_records

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    tasks = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.custom_tasks.find ( 
        { "$and": [ 
                    { 'workBy': ObjectId ( kwargs.get('current_user') ) } , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for task in result:
        tasks.append(task)
    return tasks, total_records

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    tasks = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.custom_tasks.find( 
        {"$and": [ 
                    { 'workBy': ObjectId ( kwargs.get('current_user') ) }, 
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
    for task in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        tasks.append(task)
    return tasks, total_records

# FOR THE SEARCH
def Search(*args, **kwargs):
    tasks = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.custom_tasks.find( 
        {"$and": [ 
                    { 'workBy': ObjectId ( kwargs.get('current_user') ) }, 
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
    for task in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        tasks.append(task)
    return tasks, total_records

# FOR THE FILTERS
def Filter(*args, **kwargs):
    tasks = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.custom_tasks.find ( { "$and": [ { 'workBy': ObjectId ( kwargs.get('current_user') ) } , { "$or": query_list } ] } )
    total_records = result.count()
    for task in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        tasks.append(task)
    return tasks, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    tasks = []
    # take the value from list 
    total_records = mongo.db.custom_tasks.find ( {'workBy': ObjectId ( kwargs.get('current_user') ) } ).count()
    for task in mongo.db.custom_tasks.find( {'workBy': ObjectId ( kwargs.get('current_user') ) } ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        tasks.append(task)
    return tasks, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    tasks = []
    total_records = mongo.db.custom_tasks.find ( {'workBy': ObjectId ( kwargs.get('current_user') ) } ).count()
    for task in mongo.db.custom_tasks.find( {'workBy': ObjectId ( kwargs.get('current_user') ) } ).sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        tasks.append(task)
    return tasks, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 


class CustomTasksList(Resource):
    @jwt_required
    def get(self, page):
        current_user = get_jwt_identity()
        table_rows = app.config['MAX_TABLE_ROWS']
        tasks = []
        count = page-1
        offset = table_rows*count
        total_records = mongo.db.custom_tasks.find({'workBy': ObjectId(current_user)}).count()
        for task in mongo.db.custom_tasks.find({'workBy': ObjectId(current_user)}).sort("_id", -1).limit(table_rows).skip(offset):
            tasks.append(task)
        return {'tasks': json.loads(json.dumps(tasks, default=json_util.default)), 'total_records': total_records, 'page' : page}

    @jwt_required
    def post(self, page):
        current_user = get_jwt_identity()
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        tasks = []
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
            return {'tasks': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'tasks': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'tasks': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'tasks': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'tasks': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'tasks': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'tasks': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'tasks': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}


class AddCustomTask(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = _addCustomTasks_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        id = mongo.db.custom_tasks.insert({
            'title': data['title'],
            'desc': data['desc'],
            'deadline': data['deadline'],
            'status': "On-progress",
            'workBy': ObjectId(current_user),
            'requestedDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection custom_tasks           
        # insert new notification details in notification collection                                                                                 
        return {"message": "Case requested successfully! "}, 201
    

class CustomTasksDetails(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        task_details = mongo.db.custom_tasks.find_one({'_id': ObjectId(id)})
        return json.loads(json.dumps(task_details, default=json_util.default))