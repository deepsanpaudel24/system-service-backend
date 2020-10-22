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


_timerInfo_parser =  reqparse.RequestParser()

_timerInfo_parser.add_argument('title',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_timerInfo_parser.add_argument('startingTime',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_timerInfo_parser.add_argument('stoppingTime',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_timerInfo_parser.add_argument('Timervalue',
                    type=float,
                    required=True,
                    help="This field cannot be blank."
                    )
_timerInfo_parser.add_argument('Billable',
                    type=bool,
                    required=True,
                    help="This field cannot be blank."
                    )
_timerInfo_parser.add_argument('caseId',
                    type=str,
                    required=False
                    )
                 

class AddTimer(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = _timerInfo_parser.parse_args()
        id = mongo.db.timers.insert({
            'title': data['title'],
            'startingTime': data['startingTime'],
            'stoppingTime': data['stoppingTime'],
            'Timervalue': data['Timervalue'],
            'workBy': ObjectId(current_user),
            'billable': data['Billable'],
            'caseId': ObjectId(data['caseId']),
            'createdDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection cases                                                                                            
        return {"message": "Timer added successfully! "}, 201

class TotalSpentTime(Resource):
    @jwt_required
    def get(self, caseId):
        current_user = get_jwt_identity()
        timerValues = []
        timerInfoList = mongo.db.timers.find({'workBy': ObjectId(current_user), 'caseId': ObjectId(caseId)})
        timerInfoList = json.loads(dumps(timerInfoList))
        for item in timerInfoList:
            timerValue = item['Timervalue']
            timerValues.append(timerValue)
        reduce_result = reduce(lambda num1, num2: num1 + num2, timerValues)
        reduce_result = convertTime(reduce_result)
        return reduce_result