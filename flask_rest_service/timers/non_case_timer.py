from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from functools import reduce
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
from bson import json_util
from datetime import datetime

# for conversion of milliseconds into human time
def convertTime(item):
    time = item
    days = time // (24 * 3600000)
    time = time % (24 * 3600000)
    hours = time // 3600000
    time %= 3600000
    minutes = time // (60*1000)
    time %= 60*1000
    seconds = time//1000
    time %= 1000
    miliseconds = time
    humanizeTime = {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'milliseconds':miliseconds,
    }
    return humanizeTime


_addNonCaseTimer_parser =  reqparse.RequestParser()

_addNonCaseTimer_parser.add_argument('title',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

_updateNonCaseTimer_parser =  reqparse.RequestParser()

_updateNonCaseTimer_parser.add_argument('timerValue',
                    type=float,
                    required=True,
                    help="This field cannot be blank."
                    )
                 

class AddNonCaseTimer(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = _addNonCaseTimer_parser.parse_args()
        id = mongo.db.non_case_timers.insert({
            'title': data['title'],
            'Timervalue': 0,
            'workBy': ObjectId(current_user),
            'createdDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection cases                                                                                            
        return {"message": "Timer added successfully! "}, 201

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCA" or user.get('user_type') == "SPS" or user.get('user_type') == "SPCAe":
            timers = []
            for timer in mongo.db.non_case_timers.find({'workBy': ObjectId(current_user)}):
                timer['humanizeTime'] = convertTime(timer.get('Timervalue'))
                timers.append(timer)
            return json.loads(json.dumps(timers, default=json_util.default))
        return {
            "message": "You are not authorized to view cases"
        }, 403 
    
class UpdateNonCaseTimer(Resource):
    @jwt_required
    def put(self, timerId):
        current_user = get_jwt_identity()
        data = _updateNonCaseTimer_parser.parse_args()
        current_timer = mongo.db.non_case_timers.find_one({'_id': ObjectId(timerId)})
        # add current_timer.get('Timervalue') with data['timerValue']
        mongo.db.non_case_timers.update_one({'_id': ObjectId(timerId)}, {
                '$set': {
                'Timervalue': current_timer.get('Timervalue') + data['timerValue']
            }
        })
        return {"message": "Case forwarded to all the service providers"}, 200

