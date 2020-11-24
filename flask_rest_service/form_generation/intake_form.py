from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
from bson import json_util
from datetime import datetime


# ******************************** FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 

# FOR SEARCH AND FILTER AND SORTING
def SearchandFilterandSorting(*args, **kwargs):
    forms = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.intake_forms.find( 
        {"$and": [ 
                    { 'createdBy': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "averageTimeTaken": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for service in result:
        forms.append(service)
    return forms, total_records

# FOR SEARCH AND SORTING
def SearchandSorting(*args, **kwargs):
    forms = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.intake_forms.find( 
        {"$and": [ 
                    { 'createdBy': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "averageTimeTaken": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for service in query:
        forms.append(service)
    return forms, total_records

# FOR FILTER AND SORTING
def FilterandSorting(*args, **kwargs):
    forms = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.intake_forms.find ( 
        { "$and": [ 
                    { 'createdBy': ObjectId ( kwargs.get('current_user') ) } , 
                    { "$or": query_list }
                 ] 
        } 
    ).sort(kwargs.get('sortingKey'), kwargs.get('sortingValue')).limit(kwargs.get('table_rows')).skip(kwargs.get('offset'))
    total_records = result.count()
    for service in result:
        forms.append(service)
    return forms, total_records

# FOR THE SEARCH AND THE FILTER 
def SearchandFilter(*args, **kwargs):
    forms = []
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.intake_forms.find( 
        {"$and": [ 
                    { 'createdBy': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "averageTimeTaken": { "$regex": f".*{kwargs.get('search_keyword')}.*" } }  
                            ] 
                    },
                    { "$or": query_list } 
                ] 
        } 
    )
    total_records = result.count()
    for service in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        forms.append(service)
    return forms, total_records

# FOR THE SEARCH
def Search(*args, **kwargs):
    forms = []
    # regex query to find the words in the table 
    # below query find the records in the table where email begins with the keyword coming from the user input
    query = mongo.db.intake_forms.find( 
        {"$and": [ 
                    { 'createdBy': ObjectId ( kwargs.get('current_user') ) }, 
                    { "$or": [ 
                                { "title": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } , 
                                { "createdDate": { "$regex": f".*{kwargs.get('search_keyword')}.*" , "$options" : "i" } } , 
                                { "averageTimeTaken": { "$regex": f".*{kwargs.get('search_keyword')}.*" } } 
                            ] 
                    } 
                ] 
        } 
    )
    # This gives the total number of results we have so that the frontend can work accordingly
    total_records = query.count()
    for service in query.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        forms.append(service)
    return forms, total_records

# FOR THE FILTERS
def Filter(*args, **kwargs):
    forms = []
    # take the value from list 
    query_list = []
    for filter_dict in kwargs.get('filters'):
        for x,y in filter_dict.items():
            query = { x : y}
            query_list.append(query)
    result = mongo.db.intake_forms.find ( { "$and": [ { 'createdBy': ObjectId ( kwargs.get('current_user') ) } , { "$or": query_list } ] } )
    total_records = result.count()
    for service in result.sort("_id", -1).limit(kwargs.get('table_rows')).skip(kwargs.get('offset')):
        forms.append(service)
    return forms, total_records

# FOR THE SORTING
def Sorting(*args, **kwargs):
    forms = []
    # take the value from list 
    total_records = mongo.db.intake_forms.find ( {'createdBy': ObjectId ( kwargs.get('current_user') ) } ).count()
    for service in mongo.db.intake_forms.find( {'createdBy': ObjectId ( kwargs.get('current_user') ) } ).sort( kwargs.get('sortingKey'), kwargs.get('sortingValue') ).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        forms.append(service)
    return forms, total_records

# FOR THE DEFAULT 
def InitialRecords(*args, **kwargs):
    forms = []
    total_records = mongo.db.intake_forms.find ( {'createdBy': ObjectId ( kwargs.get('current_user') ) } ).count()
    for service in mongo.db.intake_forms.find( {'createdBy': ObjectId ( kwargs.get('current_user') ) } ).sort("_id", -1).limit( kwargs.get('table_rows') ).skip( kwargs.get('offset') ):
        forms.append(service)
    return forms, total_records

# ******************************** END OF FUNCTION FOR THE DATABASE TABLE  ******************************************************* # 


class IntakeFormList(Resource):
    @jwt_required
    def get(self, page):
        current_user = get_jwt_identity()
        table_rows = app.config['MAX_TABLE_ROWS']
        forms = []
        count = page-1
        offset = table_rows*count
        total_records = mongo.db.intake_forms.find({'createdBy': ObjectId(current_user)}).count()
        for form in mongo.db.intake_forms.find({'createdBy': ObjectId(current_user)}).sort("_id", -1).limit(table_rows).skip(offset):
            forms.append(form)
        return {'forms': json.loads(json.dumps(forms, default=json_util.default)), 'total_records': total_records, 'page' : page}

    @jwt_required
    def post(self, page):
        current_user = get_jwt_identity()
        data = request.get_json()
        table_rows = app.config['MAX_TABLE_ROWS']
        forms = []
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
            return {'forms': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for search and sorting
        elif data.get('keyword') and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['search_keyword'] = data.get('keyword')
            search_filter_sorting_result = SearchandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'forms': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}

        # for filter and sorting 
        elif len(data.get('filters')) and data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            value['filters'] = data.get('filters')
            search_filter_sorting_result = FilterandSorting( **value, **data.get('sorting') ) # SearchandFilter is the function defined above 
            return {'forms': json.loads(json.dumps(search_filter_sorting_result[0], default=json_util.default)), 'total_records': search_filter_sorting_result[1], 'page' : page}   

        # this is for, incase there are both search and filters
        elif data.get('keyword') and len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            value['search_keyword'] = data.get('keyword')
            search_filter_result = SearchandFilter( **value ) # SearchandFilter is the function defined above 
            return {'forms': json.loads(json.dumps(search_filter_result[0], default=json_util.default)), 'total_records': search_filter_result[1], 'page' : page}
        
        # if there is only search    
        elif data.get('keyword'):
            value['search_keyword'] = data.get('keyword')
            search_result = Search( **value ) # Search is the function defined above 
            return {'forms': json.loads(json.dumps(search_result[0], default=json_util.default)), 'total_records': search_result[1], 'page' : page}

        # if there is only filter   
        elif len(data.get('filters')) > 0:
            value['filters'] = data.get('filters')
            filter_result = Filter( **value ) # Filter is the function defined above 
            return {'forms': json.loads(json.dumps(filter_result[0], default=json_util.default)), 'total_records': filter_result[1], 'page' : page}
        
        # if there is only sorting
        elif data.get('sorting')['sortingKey'] and data.get('sorting')['sortingValue']:
            sorting_result = Sorting( **value, **data.get('sorting') ) # Sorting is the function defined above
            return {'forms': json.loads(json.dumps(sorting_result[0], default=json_util.default)), 'total_records': sorting_result[1], 'page' : page}

        # if there is no filter and search or default
        else:
            initial_result = InitialRecords( **value ) # Filter is the function defined above 
            return {'forms': json.loads(json.dumps(initial_result[0], default=json_util.default)), 'total_records': initial_result[1], 'page' : page}


class IntakeForm(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS" or user.get("user_type") == "SPCAe":
            ClientIntakeForm = mongo.db.intake_forms.find_one({'createdBy': ObjectId(current_user)})
            if ClientIntakeForm:
                return json.loads(json.dumps(ClientIntakeForm, default=json_util.default))
            return {"message": "Intake Form not found"}, 404

    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = request.get_json()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        id = mongo.db.intake_forms.insert({
            'formFields': data['formFields'],
            'title':data['formTitle'],
            'createdBy': ObjectId(current_user),
            'createdDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection intake_forms                                                                                           
        return {"message": "Intake Form created successfully! "}, 201
    
    @jwt_required
    def put(self):
        data= request.get_json()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        mongo.db.intake_forms.update_one({'createdBy': ObjectId(current_user)}, {
                    '$set': {
                        'formFields': data['formFields']
                }
            })
        return {
            "message": "Service updated sucessfully"
        }, 200
    

class IntakeFormDetails(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS" or user.get("user_type") == "SPCAe":
            ClientIntakeForm = mongo.db.intake_forms.find_one({'_id': ObjectId(id)})
            if ClientIntakeForm:
                return json.loads(json.dumps(ClientIntakeForm, default=json_util.default))
            return {"message": "Intake Form not found"}, 404
    
    @jwt_required
    def put(self, id):
        data= request.get_json()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        mongo.db.intake_forms.update_one({'_id': ObjectId(id)}, {
                    '$set': {
                        'formFields': data['formFields']
                }
            })
        return {
            "message": "Service updated sucessfully"
        }, 200