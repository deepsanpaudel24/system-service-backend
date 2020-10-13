from flask_rest_service import app, api, mongo
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

class ServicesList(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS" or user.get('user_type') == "SPCAe":
            services = []
            for service in mongo.db.services.find({'owner': ObjectId(current_user)}):
                services.append(service)
            return json.loads(json.dumps(services, default=json_util.default))
        return {
            "message": "You are not authorized to view cases"
        }, 403 

class SaViewServicesList(Resource):
    @jwt_required
    def get(self, ownerid):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SA" or user.get('user_type') == "SAe":
            services = []
            for service in mongo.db.services.find({'owner': ObjectId(ownerid)}):
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