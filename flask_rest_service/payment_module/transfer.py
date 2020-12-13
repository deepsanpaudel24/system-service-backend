import json
import os

import stripe
#from dotenv import load_dotenv, find_dotenv
from flask import jsonify, redirect, request, session
from flask_restful import Resource, request, url_for
from flask_rest_service import app, api, mongo
from bson.objectid import ObjectId
from flask_jwt_extended import get_jwt_identity, jwt_required
from functools import reduce
from bson.json_util import dumps
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

stripe.api_key = os.getenv('STRIPE_API_KEY')



class Transfer(Resource):
    def post(self):
        data = request.get_json()
        transfer = stripe.Transfer.create(
            amount=int(data['total_payable_amount_converted'])*100,
            currency="usd",
            destination=data['destination'],
            metadata= { 
                'caseId': data['caseId'],
                'caseTitle': data['caseTitle'],
                'clientId': data['clientId'],
                'clientName': data['clientName'],
                'spId': data['spId'],
                'spName': data['spName'],
                'conversion_rate': data['conversion_rate'],
                'commission_rate': data['commission_rate'],
                'application_fee': float(data['application_fee'])*float(data['conversion_rate'])
            }
        )
        return {'message':'Transfer successfull'}, 200