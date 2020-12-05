from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime

# for conversion of milliseconds into human time
def convertTime(item):
    humanizeTime_string = ""
    time = item
    days = time // (24 * 3600000)
    time = time % (24 * 3600000)
    hours = time // 3600000
    time %= 3600000
    minutes = time // (60*1000)
    time %= 60*1000
    seconds = time//1000
    time %= 1000
    miliseconds = time
    humanizeTime = {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'milliseconds':miliseconds,
    }
    if days:
        humanizeTime_string = f"{days} days : "
    if hours:
        humanizeTime_string = humanizeTime_string + f"{hours} hours : "
    if minutes:
        humanizeTime_string = humanizeTime_string + f"{minutes} minutes : "
    if seconds:
        humanizeTime_string = humanizeTime_string + f"{seconds} seconds"

    return humanizeTime_string

# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    timers = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)

    main_condition = {'caseId': ObjectId(kwargs.get('caseId'))}

    result = mongo.db.timers.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "humanize_starting_time": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "humanize_stopping_time": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "Timervalue": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for timer in result:
        timers.append(timer)
    return timers, total_records

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    timers = []
    main_condition = {'caseId': ObjectId(kwargs.get('caseId'))}
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.timers.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "humanize_starting_time": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "humanize_stopping_time": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "Timervalue": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for timer in query:
        timers.append(timer)
    return timers, total_records

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    timers = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    
    main_condition = {'caseId': ObjectId(kwargs.get('caseId'))}

    result = mongo.db.timers.find ( 
        { "$and": [ 
                    main_condition , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for timer in result:
        timers.append(timer)
    return timers, total_records

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    timers = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    main_condition = {'caseId': ObjectId(kwargs.get('caseId'))}
    result = mongo.db.timers.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "humanize_starting_time": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "humanize_stopping_time": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "Timervalue": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    )
    total_records = result.count()
    for timer in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        timers.append(timer)
    return timers, total_records

# FOR THE SEARCH
def Search(*args, **kwargs):
    timers = []

    main_condition = {'caseId': ObjectId(kwargs.get('caseId'))}

    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.timers.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "humanize_starting_time": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "humanize_stopping_time": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "Timervalue": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    )
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for timer in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        timers.append(timer)
    return timers, total_records

# FOR THE FILTERS
def Filter(*args, **kwargs):
    timers = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    
    main_condition = {'caseId': ObjectId(kwargs.get('caseId'))}
    result = mongo.db.timers.find ( { "$and": [ main_condition , { "$or": query_list } ] } )
    total_records = result.count()
    for timer in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        timers.append(timer)
    return timers, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    timers = []

    main_query = mongo.db.timers.find({'caseId': ObjectId(kwargs.get('caseId'))})

    # take the value from list 
    total_records = main_query.count()
    for timer in main_query.sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        timers.append(timer)
    return timers, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    timers = []
    main_query = mongo.db.timers.find({'caseId': ObjectId(kwargs.get('caseId'))})
    total_records = main_query.count()
    for timer in main_query.sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        timers.append(timer)
    return timers, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

class CaseTimersList(Resource):
    @jwt_required
    def get(self, page, caseId):
        current_user = get_jwt_identity()
        user_details = mongo.db.users.find_one( { '_id': ObjectId(current_user) } )
        table_rows = app.config['MAX_TABLE_ROWS']
        timers = []
        count = page-1
        offset = table_rows*count
    
        main_query = mongo.db.timers.find({'caseId': ObjectId(caseId) })

        total_records = main_query.count()
        for timer in main_query.sort("_id", -1).limit(table_rows).skip(offset):
            humanize_timer_value = convertTime(timer.get('Timervalue'))
            timer['humanize_timerValue'] = humanize_timer_value
            timers.append(timer)
        return {'timers': json.loads(json.dumps(timers, default=json_util.default)), 'total_records': total_records, 'page' : page}

    @jwt_required
    def post(self, page, caseId):
        current_user = get_jwt_identity()
        user_details = mongo.db.users.find_one( { '_id': ObjectId(current_user) } )
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        timers = []
        count = page-1
        offset = table_rows*count
        value  = {
            "current_user": current_user,
            "table_rows": table_rows,
            "offset": offset,
            "caseId": caseId
        }

        # for all three , search, filter and sorting
        if data.get('keyword') and len(data.get('filters')) > 0 and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandFilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'timers': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'timers': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'timers': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'timers': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'timers': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'timers': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'timers': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'timers': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}
