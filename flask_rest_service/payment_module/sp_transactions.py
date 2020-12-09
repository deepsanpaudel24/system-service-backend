import os
import stripe
from flask import jsonify
from flask_restful import Resource, request, url_for
from flask_rest_service import app, api, mongo
from bson.objectid import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from bson import json_util


# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    transactions = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)

    main_condition = { "$or" : [ {'serviceProviderId': ObjectId(kwargs.get('current_user'))}, {'clientId': ObjectId(kwargs.get('current_user'))} ]}

    result = mongo.db.checkout_transactions.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "payment_date": { "$regex": f".*{kwargs.get('search_keyword')}.*", "$options" : "i" } } , 
                                { "amount": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "currency": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } }
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for transaction in result:
        transactions.append(transaction)
    return transactions, total_records

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    transactions = []
    main_condition = { "$or" : [ {'serviceProviderId': ObjectId(kwargs.get('current_user'))}, {'clientId': ObjectId(kwargs.get('current_user'))} ]}
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.checkout_transactions.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "payment_date": { "$regex": f".*{kwargs.get('search_keyword')}.*", "$options" : "i" } } , 
                                { "amount": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "currency": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } }
                            ] 
                    } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for transaction in query:
        transactions.append(transaction)
    return transactions, total_records

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    transactions = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    
    main_condition = { "$or" : [ {'serviceProviderId': ObjectId(kwargs.get('current_user'))}, {'clientId': ObjectId(kwargs.get('current_user'))} ]}

    result = mongo.db.checkout_transactions.find ( 
        { "$and": [ 
                    main_condition , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for transaction in result:
        transactions.append(transaction)
    return transactions, total_records

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    transactions = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    main_condition = { "$or" : [ {'serviceProviderId': ObjectId(kwargs.get('current_user'))}, {'clientId': ObjectId(kwargs.get('current_user'))} ]}

    result = mongo.db.checkout_transactions.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "payment_date": { "$regex": f".*{kwargs.get('search_keyword')}.*", "$options" : "i" } } , 
                                { "amount": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "currency": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } }
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    )
    total_records = result.count()
    for transaction in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        transactions.append(transaction)
    return transactions, total_records

# FOR THE SEARCH
def Search(*args, **kwargs):
    transactions = []
    main_condition = { "$or" : [ {'serviceProviderId': ObjectId(kwargs.get('current_user'))}, {'clientId': ObjectId(kwargs.get('current_user'))} ]}

    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.checkout_transactions.find( 
        {"$and": [ 
                    main_condition, 
                    { "$or": [ 
                                { "payment_date": { "$regex": f".*{kwargs.get('search_keyword')}.*", "$options" : "i" } } , 
                                { "amount": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "currency": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } }
                            ] 
                    } 
                ] 
        } 
    )
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for transaction in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        transactions.append(transaction)
    return transactions, total_records

# FOR THE FILTERS
def Filter(*args, **kwargs):
    transactions = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    
    main_condition = { "$or" : [ {'serviceProviderId': ObjectId(kwargs.get('current_user'))}, {'clientId': ObjectId(kwargs.get('current_user'))} ]}

    result = mongo.db.checkout_transactions.find ( { "$and": [ main_condition , { "$or": query_list } ] } )
    total_records = result.count()
    for transaction in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        transactions.append(transaction)
    return transactions, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    transactions = []

    main_query = mongo.db.checkout_transactions.find({ "$or" : [ {'serviceProviderId': ObjectId(kwargs.get('current_user'))}, {'clientId': ObjectId(kwargs.get('current_user'))} ]})

    # take the value from list 
    total_records = main_query.count()
    for transaction in main_query.sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        transactions.append(transaction)
    return transactions, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    transactions = []

    main_query = mongo.db.checkout_transactions.find( { "$or" : [ {'serviceProviderId': ObjectId(kwargs.get('current_user'))}, {'clientId': ObjectId(kwargs.get('current_user'))} ]} )

    total_records = main_query.count()
    for transaction in main_query.sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        transactions.append(transaction)
    return transactions, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

class SPTransactions(Resource):
    @jwt_required
    def get(self, page): 
        current_user = get_jwt_identity()
        user_details = mongo.db.users.find_one( { '_id': ObjectId(current_user) } )
        table_rows = app.config['MAX_TABLE_ROWS']
        transactions = []
        count = page-1
        offset = table_rows*count
        main_query = mongo.db.checkout_transactions.find( { "$or" : [ {'serviceProviderId': ObjectId(current_user)}, {'clientId': ObjectId(current_user)} ]} )
        total_records = main_query.count()
        for transaction in main_query.sort("_id", -1).limit(table_rows).skip(offset):
            transactions.append(transaction)
        return {'transactions': json.loads(json.dumps(transactions, default=json_util.default)), 'total_records': total_records, 'page' : page}

    @jwt_required
    def post(self, page):
        current_user = get_jwt_identity()
        user_details = mongo.db.users.find_one( { '_id': ObjectId(current_user) } )
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        checkout_transactions = []
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
            return {'transactions': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'transactions': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'transactions': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'transactions': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'transactions': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'transactions': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'transactions': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'transactions': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}


class SPCaseTransactions(Resource):
    @jwt_required
    def get(self, caseId): 
        current_user = get_jwt_identity()
        user_details = mongo.db.users.find_one( { '_id': ObjectId(current_user) } )
        transactions = []
        if user_details.get('user_type') == "SPCAe":
            main_query = mongo.db.checkout_transactions.find({'serviceProviderId': ObjectId(user_details.get('owner')), 'caseId': ObjectId(caseId)})
        else:
            main_query = mongo.db.checkout_transactions.find({'serviceProviderId': ObjectId(current_user), 'caseId': ObjectId(caseId)})
        for transaction in main_query.sort("_id", -1):
            transactions.append(transaction)
        return {'transactions': json.loads(json.dumps(transactions, default=json_util.default))}