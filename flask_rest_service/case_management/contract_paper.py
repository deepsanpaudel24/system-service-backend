from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
import werkzeug
from werkzeug.utils import secure_filename
from bson import json_util
from datetime import datetime
import os
import uuid
from flask_rest_service.notifications import InsertNotifications

_parse = reqparse.RequestParser()

_UploadContractPaper_parser =  reqparse.RequestParser()

_UploadContractPaper_parser.add_argument('title',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                    )
_UploadContractPaper_parser.add_argument('desc',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )

class UploadContractPaper(Resource):
    @jwt_required
    def post(self, caseId):
        current_user = get_jwt_identity()
        data = _UploadContractPaper_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCAe":
            user = mongo.db.users.find_one({'_id': ObjectId(user.get('owner'))})
        case_details = mongo.db.cases.find_one({'_id': ObjectId(caseId)})

        myFiles = request.files
        for key in myFiles:
            _parse.add_argument(
                key, type=werkzeug.datastructures.FileStorage, location='files')
        args = _parse.parse_args()
        filesLocationList = []
        for key in myFiles:
            file = args[key]
            filename = secure_filename(file.filename)
            filename, extension = filename.split('.')
            filename = f"{filename}-{uuid.uuid4().hex}.{extension}"
            dirToSaveFile = '/'.join(app.config['UPLOAD_FOLDER'].split('/')[1:])
            filesLocationList.append(f"{dirToSaveFile}/{filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        id = mongo.db.contracts.insert({
            'title': data['title'],
            'desc': data['desc'],
            'caseId': ObjectId(caseId),
            'files': filesLocationList,
            'uploadDate': datetime.today().strftime('%Y-%m-%d')
        })
        mongo.db.cases.update_one({'_id': ObjectId(caseId)}, {
            '$set': {
                'status': "Contract-Sent"
            }
        })   
        # Send notifiations to the client saying they received the contract paper from service provider. 
        notification_values = {
            "title" : f"{user.get('name')} has sent a contract paper.",
            "sender": ObjectId(current_user),
            "receiver": case_details.get('client'),
            "link": f"/user/case/{caseId}"
        } 
        InsertNotifications(**notification_values)                                                                              
        return {"message": "Contract paper uploaded successfully! "}, 201

class ConfirmContractPaper(Resource):
    @jwt_required
    def put(self, caseId):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCAe":
            user = mongo.db.users.find_one({'_id': ObjectId(user.get('owner'))})
        case = mongo.db.cases.find_one({'_id': ObjectId(caseId)})
        if case:
            if case.get('paymentType') == "advance-payment":
                mongo.db.cases.update_one({'_id': ObjectId(caseId)}, {
                '$set': {
                    'status': "Awaiting-Advance-Payment"
                }
            })
            else:
                mongo.db.cases.update_one({'_id': ObjectId(caseId)}, {
                    '$set': {
                        'status': "On-progress"
                    }
                })
            # Send notifiations to the client saying they received the contract paper from service provider. 
            notification_values = {
                "title" : f"{user.get('name')} has confirmed a contract.",
                "sender": ObjectId(current_user),
                "receiver": case.get('client'),
                "link": f"/user/case/{caseId}"
            } 
            InsertNotifications(**notification_values)   
            return { "message": "Contract confirmed Sucessfully"}, 200  
        return {"message": "case not found"}, 404

class ContractDetails(Resource):
    @jwt_required
    def get(self, caseId):
        current_user = get_jwt_identity()
        contract_details = mongo.db.contracts.find_one({'caseId': ObjectId(caseId)})
        return json.loads(json.dumps(contract_details, default=json_util.default))

    @jwt_required
    def put(self, caseId):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "CCAe":
            user = mongo.db.users.find_one({'_id': ObjectId(user.get('owner'))})
        case_details = mongo.db.cases.find_one({'_id': ObjectId(caseId)})

        myFiles = request.files
        for key in myFiles:
            _parse.add_argument(
                key, type=werkzeug.datastructures.FileStorage, location='files')
        args = _parse.parse_args()
        filesLocationList = []
        for key in myFiles:
            file = args[key]
            filename = secure_filename(file.filename)
            filename, extension = filename.split('.')
            filename = f"{filename}-{uuid.uuid4().hex}.{extension}"
            dirToSaveFile = '/'.join(app.config['UPLOAD_FOLDER'].split('/')[1:])
            filesLocationList.append(f"{dirToSaveFile}/{filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if user:
            mongo.db.contracts.update_one({'caseId': ObjectId(caseId)}, {
                    '$set': {
                    'signedFiles': filesLocationList,
                    'SignedFileUploadDate': datetime.today().strftime('%Y-%m-%d')
                }
            })
            mongo.db.cases.update_one({'_id': ObjectId(caseId)}, {
                '$set': {
                    'status': "Contract-Replied"
                }
            })
            # Send notifiations to the service providers with the message saying they received the signed contract paper from the client. 
            notification_values = {
                "title" : f"{user.get('name')} has sent a signed contract paper.",
                "sender": ObjectId(current_user),
                "receiver": case_details.get('serviceProvider'),
                "link": f"/user/case/{caseId}"
            } 
            InsertNotifications(**notification_values)
            return {"message": "File uploaded sucessfully"}, 200
        return {
            "message": "User does not exist"
        }, 400