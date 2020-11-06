from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
from bson import json_util

_forwardTo_parser = reqparse.RequestParser()

_forwardTo_parser.add_argument('service_providers',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )

class Cases(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA":
            cases = []
            for case in mongo.db.cases.find().sort("_id", -1):
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
            for case in mongo.db.cases.find({'client': ObjectId(current_user)}).sort("_id", -1):
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
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS" or user.get('user_type') == "SPCAe":
            cases = []
            for case in mongo.db.cases.find({"forwardTo": { "$elemMatch" : {"$eq" : ObjectId(current_user) } } }).sort("_id", -1):
                # proposal = mongo.db.proposals.find_one({'caseId': case.get('_id'), 'serviceProvider': ObjectId(current_user)})
                # # If proposal exists, then send proposal status in response.
                # case['proposalStatus'] = proposal.get('status')
                cases.append(case)
            return json.loads(json.dumps(cases, default=json_util.default))
        return {
            "message": "You are not authorized to view cases"
        }, 403

class EmployeeCases(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCAe" or user.get('user_type') == "CCAe":
            cases = []
            for case in mongo.db.cases.find({"assigned_employee_list": { "$elemMatch" : {"$eq" : ObjectId(current_user) } } }).sort("_id", -1):
                cases.append(case)
            return json.loads(json.dumps(cases, default=json_util.default))
        return {
            "message": "You are not authorized to view cases"
        }, 403

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
            result  = mongo.db.users.find(
                { "service_categories": { "$elemMatch": { "$in": case_details.get('caseTags') } } }
                )

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
            return {"message": "Case forwarded to all the service providers"}, 200
        return {
            "user_type": str(user.get('user_type'))
        }, 403
            