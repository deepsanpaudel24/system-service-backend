import os
from flask_rest_service import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import jwt_required, get_jwt_claims

class Profile(Resource):
    @jwt_required
    def get(self):
        claims = get_jwt_claims()
        return {
            "message": "Now user set up profile",
            "user_type": claims['user_type']
        }
