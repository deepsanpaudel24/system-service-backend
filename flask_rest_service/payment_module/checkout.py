import os
import stripe
from flask import jsonify
from flask_restful import Resource, request, url_for
from flask_rest_service import app, api, mongo
from bson.objectid import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity
# Set your secret key. Remember to switch to your live secret key in production!
# See your keys here: https://dashboard.stripe.com/account/apikeys

stripe.api_key = 'sk_test_51HrMHgE8BAcK1TWiC1rrReLpfQm05TZvk5c0hfIlnuVZp2sTp78CANnR6QTfz3snvPHXlEfZKwc7gyzBkW0sX1CP00uNx2v3X2'
price_Id = "price_1HtFJGE8BAcK1TWiHmx4pGyD" 

def CalulateAdvancePaymentAmount(*args, **kwargs):
    case_details = mongo.db.cases.find_one( { '_id': ObjectId( kwargs.get('caseId') ) } )
    if case_details.get('rateType') == "hourly":
        total_amount = float(case_details.get('rate').split(' ')[0])*int(case_details.get('averageTimeTaken'))
    else:
        total_amount = float(case_details.get('rate').split(' ')[0])
    db_currency = case_details.get('rate').split(' ')[-1]
    if db_currency == "pound":
        currency = "gbp"
    elif db_currency == "euro":
        currency = "eur"
    else :
        currency = "usd"
    advance_payment_percentage = case_details.get('advancePayment')
    advance_payment_amount = (advance_payment_percentage / 100)*total_amount
    data = {
        'currency': currency,
        'amount': int(advance_payment_amount),
        'total_amount': total_amount,
        'humanize_currency': db_currency
    }
    return data


def CalulateFinalPaymentAmount(*args, **kwargs):
    case_details = mongo.db.cases.find_one( { '_id': ObjectId( kwargs.get('caseId') ) } )
    if case_details.get('rateType') == "hourly":
        total_amount = float(case_details.get('rate').split(' ')[0])*int(case_details.get('averageTimeTaken'))
    else:
        total_amount = float(case_details.get('rate').split(' ')[0])
    db_currency = case_details.get('rate').split(' ')[-1]
    if db_currency == "pound":
        currency = "gbp"
    elif db_currency == "euro":
        currency = "eur"
    else :
        currency = "usd"
    advance_payment_percentage = case_details.get('advancePayment')
    advance_payment_amount = (advance_payment_percentage / 100)*total_amount
    final_payment_amount = total_amount - advance_payment_amount
    data = {
        'currency': currency,
        'amount': int(final_payment_amount),
        'total_amount': total_amount,
        'humanize_currency': db_currency
    }
    return data


class create_checkout_session(Resource):
    @jwt_required
    def post(self):
        data = request.get_json()
        if data['caseStatus'] == "Confirm-Completion" : 
            result = CalulateFinalPaymentAmount(caseId = data['caseId'])
        else:
            result = CalulateAdvancePaymentAmount(caseId = data['caseId'])
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                    "name": data['caseTitle'],
                    "quantity": 1,
                    "currency": result['currency'],
                    "amount": result['amount']*100,
                }],
            metadata= { 
                'caseId': data['caseId'],
                'caseTitle': data['caseTitle'],
                'clientId': data['clientId'],
                'clientName': data['clientName'],
                'serviceProviderId': data['serviceProviderId'],
                'serviceProvidername': data['serviceProvidername'],
                'total_amount': result['total_amount'],
                'caseStatus': data['caseStatus'],
                'humanize_currency': result['humanize_currency']
            },
            mode='payment',
            success_url='http://localhost:3000/user/cases',
            cancel_url='http://localhost:3000',
        )

        return jsonify(id=checkout_session.id)

class create_subscription_checkout_session(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                     "price": price_Id,
                    # For metered billing, do not pass quantity
                    "quantity": 1
                }],
            metadata= { 
                'current_user': current_user,
            },
            mode="subscription",
            success_url='http://localhost:3000/user/home',
            cancel_url='http://localhost:3000',
        )

        return jsonify(id=checkout_session.id)