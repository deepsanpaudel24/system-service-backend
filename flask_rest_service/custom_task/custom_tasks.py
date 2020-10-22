from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime


_addCustomTasks_parser =  reqparse.RequestParser()

_addCustomTasks_parser.add_argument('title',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                    )
_addCustomTasks_parser.add_argument('desc',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )
_addCustomTasks_parser.add_argument('deadline',
                        type=str,
                        required=False,
                        help="This field cannot be blank."
                    )

class AddCustomTask(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = _addCustomTasks_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        id = mongo.db.custom_tasks.insert({
            'title': data['title'],
            'desc': data['desc'],
            'deadline': data['deadline'],
            'status': "On-progress",
            'workBy': ObjectId(current_user),
            'requestedDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection custom_tasks           
        # insert new notification details in notification collection                                                                                 
        return {"message": "Case requested successfully! "}, 201
    
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        tasks = []
        for task in mongo.db.custom_tasks.find({'workBy': ObjectId(current_user)}).sort("_id", -1):
            tasks.append(task)
        return json.loads(json.dumps(tasks, default=json_util.default))

class CustomTasksDetails(Resource):
    @jwt_required
    def get(self, id):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        task_details = mongo.db.custom_tasks.find_one({'_id': ObjectId(id)})
        return json.loads(json.dumps(task_details, default=json_util.default))