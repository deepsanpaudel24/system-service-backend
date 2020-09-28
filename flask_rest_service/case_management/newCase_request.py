from flask_rest_service import app, api, mongo
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime


_newCaseRequest_parser =  reqparse.RequestParser()

_newCaseRequest_parser.add_argument('title',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_newCaseRequest_parser.add_argument('type',
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
                    type=int,
                    required=False,
                    help="This field cannot be blank."
                    )

class AddNewCaseRequest(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = _newCaseRequest_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        id = mongo.db.cases.insert({
            'title': data['title'],
            'type': data['type'],
            'desc': data['desc'],
            'budgetClient': data['budget'],
            'status': "Requested",
            'client': ObjectId(current_user),
            'clientName': user.get('name'),
            'requestedDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection cases                                                                                            
        return {"message": "Case requested successfully! "}, 201