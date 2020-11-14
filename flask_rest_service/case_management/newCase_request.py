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

_newCaseRequest_parser =  reqparse.RequestParser()

_newCaseRequest_parser.add_argument('title',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                    )
_newCaseRequest_parser.add_argument('desc',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )
_newCaseRequest_parser.add_argument('budget',
                        type=str,
                        required=False,
                        help="This field is blank."
                    )
_newCaseRequest_parser.add_argument('deadline',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )
_newCaseRequest_parser.add_argument('caseTags',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )
# _newCaseRequest_parser.add_argument(
#     'sentFiles', type=werkzeug.datastructures.FileStorage, location='files')

class AddNewCaseRequest(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = _newCaseRequest_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "CCA" or user.get('user_type') == "CS":
            userType = "c"
        else:
            userType = "sp"
        caseTags = data['caseTags'].split(',')

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
            filename = f"{filename}-{uuid.uuid4().hex}.{userType}.{extension}"
            dirToSaveFile = '/'.join(app.config['UPLOAD_FOLDER'].split('/')[1:])
            filesLocationList.append(f"{dirToSaveFile}/{filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        id = mongo.db.cases.insert({
            'title': data['title'],
            'desc': data['desc'],
            'budgetClient': data['budget'],
            'deadline': data['deadline'],
            'caseTags': caseTags,
            'status': "Requested",
            'client': ObjectId(current_user),
            'clientName': user.get('name'),
            'files': filesLocationList,
            'requestedDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection cases           
        #superadmin = ObjectId("5f7196d7be625540246db3d7")      
        # Send notifiations to the super admin with the message saying client requested the new case . 
        notification_values = {
            "title" : f"A new case has been requested by the client {user.get('name')}",
            "sender": ObjectId(current_user),
            "receiver": ObjectId("5f7196d7be625540246db3d7"),
            "link": f"/sadmin/case/{id}"
        } 
        InsertNotifications(**notification_values)                 
        return {"message": "Case requested successfully! "}, 201


class UpdateRelatedDocuments(Resource):
    @jwt_required
    def put(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "CCA" or user.get('user_type') == "CS":
            userType = "c"
        else:
            userType = "sp"
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
            filename = f"{filename}-{uuid.uuid4().hex}.{userType}.{extension}"
            dirToSaveFile = '/'.join(app.config['UPLOAD_FOLDER'].split('/')[1:])
            filesLocationList.append(f"{dirToSaveFile}/{filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        case_details = mongo.db.cases.find_one({'_id': ObjectId(id)})
        allFilesLocationList = case_details.get('files') + filesLocationList
        mongo.db.cases.update_one({'_id': ObjectId(id)}, {
            '$set': {
                'files': allFilesLocationList
            }
        })
        return {"message": "Case updated successfully"}, 200

class DeleteRelatedDocuments(Resource):
    @jwt_required
    def put(self, id):
        current_user = get_jwt_identity()
        data = request.get_json()
        case_details = mongo.db.cases.find_one({'_id': ObjectId(id)})
        allFilesLocationList = data['file']
        filesFromDb = case_details.get('files')
        filesFromDb.remove(allFilesLocationList)
        mongo.db.cases.update_one({'_id': ObjectId(id)}, {
            '$set': {
                'files': filesFromDb
            }
        })
        return {"message": "Case updated successfully"}, 200