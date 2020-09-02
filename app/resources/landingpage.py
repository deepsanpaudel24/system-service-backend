from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_claims

class LandingPage(Resource):
    @jwt_required
    def get(self):
        claims = get_jwt_claims()
        return {
            "message": "Welcome to Landing Page! Please Sign up to continue",
            "user type": claims['user_type']
        }