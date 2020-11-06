from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
from bson import json_util
from datetime import datetime

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
    

class IntakeFormList(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        intakeForms = []
        for form in mongo.db.intake_forms.find({'createdBy': ObjectId(current_user)}).sort("_id", -1):
            intakeForms.append(form)
        return json.loads(json.dumps(intakeForms, default=json_util.default))

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