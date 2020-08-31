from flask import Flask
from flask_restful import Api

from app.resources.landingpage import LandingPage

app= Flask(__name__)
api = Api(app)

api.add_resource(LandingPage, '/')
