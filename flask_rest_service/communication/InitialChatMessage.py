from flask_rest_service import app, api, mongo
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson.json_util import dumps
from datetime import datetime


class InitialChatMessage(Resource):
    @jwt_required
    def get(self, room):
        current_user = get_jwt_identity()
        query_obj = {"room": room}
        all_messages = mongo.db.messages.find(
            query_obj).sort("_id", -1).limit(5)
        all_message = json.loads(dumps(all_messages))[::-1]
        return all_message
