from flask_rest_service import app, api, mongo
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util


class Cases(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA":
            cases = []
            for case in mongo.db.cases.find():
                cases.append(case)
            return json.loads(json.dumps(cases, default=json_util.default))
        return {
            "message": "You are not authorized to view clients"
        }, 403


class ClientCases(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "CCA" or user.get('user_type') == "CS":
            cases = []
            for case in mongo.db.cases.find({'client': ObjectId(current_user)}):
                cases.append(case)
            return json.loads(json.dumps(cases, default=json_util.default))
        return {
            "message": "You are not authorized to view cases"
        }, 403 

class ServiceProviderCases(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS":
            cases = []
            for case in mongo.db.cases.find({'forward': True}):
                cases.append(case)
            return json.loads(json.dumps(cases, default=json_util.default))
        return {
            "message": "You are not authorized to view cases"
        }, 403

# this case details can be viewed either by the SA or the respective client 
# or if the SP and its employee are assigned 
class ClientCasesDetails(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "CCA" or user.get('user_type') == "CS":
            case_details = mongo.db.cases.find_one({'_id': ObjectId(id)})
            return json.loads(json.dumps(case_details, default=json_util.default))
        return {"message" : "You are not authorized to view this page"}, 403


class ServiceProviderCasesDetails(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS":
            case_details = mongo.db.cases.find_one({'_id': ObjectId(id)})
            return json.loads(json.dumps(case_details, default=json_util.default))
        return {"message" : "You are not authorized to view this page"}, 403

class ForewardCaseRequest(Resource):
    @jwt_required
    def put(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA":
            mongo.db.cases.update_one({'_id': ObjectId(id)}, {
                    '$set': {
                    'forward':True
                }
            })
            return {"message": "Case forwarded to all the service providers"}
        return {
            "user_type": str(user.get('user_type'))
        }, 403
            