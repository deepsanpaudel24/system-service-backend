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
        caseTags = data['caseTags'].split(',')

        # files = data['sentFiles']
        # filename = secure_filename(files.filename)
        # files.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        myFiles = request.files
        for key in myFiles:
            _parse.add_argument(
                key, type=werkzeug.datastructures.FileStorage, location='files')
        args = _parse.parse_args()
        filesLocationList = []
        for key in myFiles:
            file = args[key]
            filename = secure_filename(file.filename)
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
        # insert new notification details in notification collection
        # needs to palce the superadmin id in env varaibles
        id = mongo.db.notifications.insert({
            'title': "New service request from " + user.get('name'),
            'sender': ObjectId(current_user),
            'receiver': ObjectId("5f7196d7be625540246db3d7"),
            'status': 'unread',
            'createdDate': datetime.today().strftime('%Y-%m-%d')
        })                                                                                 
        return {"message": "Case requested successfully! "}, 201