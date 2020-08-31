from flask_restful import Resource

class LandingPage(Resource):
    def get(self):
        return {"message": "Welcome to Landing Page!"}