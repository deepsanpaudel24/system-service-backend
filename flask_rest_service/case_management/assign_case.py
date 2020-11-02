from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime
import os
import werkzeug
from werkzeug.utils import secure_filename


_assignCase_parser =  reqparse.RequestParser()

_assignCase_parser.add_argument('employeeId',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_assignCase_parser.add_argument('case_assignment',
                    type=bool,
                    required=True,
                    help="This field cannot be blank."
                    )

class EmployeeCaseAssignment(Resource):
    @jwt_required
    def put(self, caseId):
        current_user = get_jwt_identity()
        data = request.get_json()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        assigned_emp_list = list(map(lambda x: ObjectId(x), data['assigned_employee_list']))
        if user: 
            case = mongo.db.cases.find_one({'_id': ObjectId(caseId)})
            if case: 
                mongo.db.cases.update_one({'_id': ObjectId(caseId)}, {
                    '$set': {
                        'assigned_employee_list': assigned_emp_list
                        }
                    })
                return { "message": "Case assigned Sucessfully"}, 200
            return {"message": "Case does not exist"}, 404
        return { "message": "User does not exist"}, 404