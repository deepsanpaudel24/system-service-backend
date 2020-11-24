import os
from flask import jsonify
from flask_rest_service import app, api, mongo, mail
# from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import jwt_required, get_jwt_claims, get_jwt_identity
from bson.objectid import ObjectId
import json
from bson import json_util
import werkzeug
from werkzeug.utils import secure_filename
import uuid


_parse = reqparse.RequestParser()

_intro_text_parser =  reqparse.RequestParser()

_intro_text_parser.add_argument('intro_text',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                    )

class ProfileSettingUpdate(Resource):
    @jwt_required
    def put(self):
        data= request.get_json()
        values = list(data.items())[0]
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            if values[0] == "service_categories":
                service_tags = data['service_categories'].split(',')
                mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                    '$set': {
                    values[0]: service_tags
                    }
                })
            else :
                mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                        '$set': {
                        values[0]: values[1]
                    }
                })
            return {"message": "Details upated sucessfully"}, 200
        return {
            "message": "User does not exist"
        }, 400

class ProfileIntroductionUpdate(Resource):
    @jwt_required
    def put(self):
        data= _intro_text_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})

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
            dirToSaveFile = '/'.join(app.config['UPLOAD_FOLDER_VIDEO'].split('/')[1:])
            filesLocationList.append(f"{dirToSaveFile}/{filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER_VIDEO'], filename))
        
        print("value of data", data)

        if user:
            if data['intro_text'] and filesLocationList:
                mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                        '$set': {
                        "intro_text": data['intro_text'],
                        "intro_video": filesLocationList
                    }
                })

            elif filesLocationList:
                mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                        '$set': {
                        "intro_video": filesLocationList
                    }
                })
            elif data['intro_text']:
                mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                        '$set': {
                        "intro_text": data['intro_text']
                    }
                })
            else :
                return { "message": "Could not update the introduction"}, 400
            return {"message": "Details upated sucessfully"}, 200
        return {
            "message": "User does not exist"
        }, 400