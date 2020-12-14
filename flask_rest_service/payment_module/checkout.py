import os
import stripe
from flask import jsonify
from flask_restful import Resource, request, url_for
from flask_rest_service import app, api, mongo
from bson.objectid import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
# Set your secret key. Remember to switch to your live secret key in production!
# See your keys here: https://dashboard.stripe.com/account/apikeys

stripe.api_key = os.getenv('STRIPE_API_KEY')
annual_price_Id = os.getenv('ANNUAL_PRICE_ID')
monthly_price_Id = os.getenv('MONTHLY_PRICE_ID')


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
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "CCAe":
            current_user = user.get('owner')
        data = request.get_json()
        if data['caseStatus'] == "Confirm-Completion" : 
            result = CalulateFinalPaymentAmount(caseId = data['caseId'])
        else:
            result = CalulateAdvancePaymentAmount(caseId = data['caseId'])

        advance_payment_details = mongo.db.checkout_transactions.find_one({'clientId': ObjectId(current_user), 'caseId': ObjectId(data['caseId'])})
        if advance_payment_details:
            advance_amount = advance_payment_details.get('paid_amount')
        else:
            advance_amount = 0
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
                'humanize_currency': result['humanize_currency'],
                'advance_amount': advance_amount
            },
            mode='payment',
            success_url=os.getenv('FRONTEND_DOMAIN')+'/user/cases',
            cancel_url=os.getenv('FRONTEND_DOMAIN'),
        )

        return jsonify(id=checkout_session.id)

class create_subscription_checkout_session(Resource):
    @jwt_required
    def post(self, type):
        if type == "monthly":
            price_Id = monthly_price_Id
        else:
            price_Id = annual_price_Id
        current_user = get_jwt_identity()

        user_details = mongo.db.users.find_one( { '_id': ObjectId(current_user)} )
        if user_details.get('user_type') == "SPCA" or user_details.get('user_type') == "CCA":
            no_employees = mongo.db.users.find({ 'owner': ObjectId(current_user)}).count()
        else:
            no_employees = 0
        total_quantity = no_employees + 1
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                    "price": price_Id,
                    # For metered billing, do not pass quantity
                    "quantity": total_quantity
                }],
            metadata= { 
                'current_user': current_user,
                'clientName': user_details.get('name'),
                'subscribe_type': type
            },
            mode="subscription",
            success_url=os.getenv('FRONTEND_DOMAIN')+'/user/home',
            cancel_url=os.getenv('FRONTEND_DOMAIN'),
        )

        return jsonify(id=checkout_session.id)

class create_subscription_checkout_session_from_login(Resource):
    def post(self, type, email):
        if type == "monthly":
            price_Id = monthly_price_Id
        else:
            price_Id = annual_price_Id
        user_details = mongo.db.users.find_one( { 'email': email} )
        if user_details.get('user_type') == "SPCA" or user_details.get('user_type') == "CCA":
            no_employees = mongo.db.users.find({ 'owner': ObjectId(user_details.get('_id'))}).count()
        else:
            no_employees = 0
        total_quantity = no_employees + 1
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                    "price": price_Id,
                    # For metered billing, do not pass quantity
                    "quantity": total_quantity
                }],
            metadata= { 
                'current_user': user_details.get('_id'),
                'clientName': user_details.get('name'),
                'subscribe_type': type
            },
            mode="subscription",
            success_url=os.getenv('FRONTEND_DOMAIN')+'/user/home',
            cancel_url=os.getenv('FRONTEND_DOMAIN'),
        )

        return jsonify(id=checkout_session.id)