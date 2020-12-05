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

# Setup Stripe python client library
# load_dotenv(find_dotenv())
# stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = 'sk_test_51HrMHgE8BAcK1TWiC1rrReLpfQm05TZvk5c0hfIlnuVZp2sTp78CANnR6QTfz3snvPHXlEfZKwc7gyzBkW0sX1CP00uNx2v3X2'


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
            }
        )
        return {'message':'Transfer successfull'}, 200