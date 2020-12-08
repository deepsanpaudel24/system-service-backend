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

def CalculateTotalBillableHourCase(id):
    # find the total billable time for this case
    timerValues = []
    timerInfoList = mongo.db.timers.find({'caseId': ObjectId(id), 'billable':True})
    timerInfoList = json.loads(dumps(timerInfoList))
    for item in timerInfoList:
        timerValue = item['Timervalue']
        timerValues.append(timerValue)
    reduce_result = reduce(lambda num1, num2: num1 + num2, timerValues)
    reduce_result = convertTime(reduce_result)
    total_hour = reduce_result.get('day')*24 + reduce_result.get('hour') + (reduce_result.get('minute')/ 60) + (reduce_result.get('seconds')/ 3600)
    return total_hour


class TransferInfo(Resource):
    @jwt_required
    def get(self, id):
        case_details = mongo.db.cases.find_one( { '_id': ObjectId(id) } )
        if case_details: 
            if case_details.get('rate') == "hourly":
                total_hour = CalculateTotalBillableHourCase(id)
                total_case_fee = float(case_details.get('rate').split(' ')[0]) * total_hour
            else:
                total_case_fee = float(case_details.get('rate').split(' ')[0]) 
            
            # calculating the total application fee
            service_provider_details = mongo.db.users.find_one( { '_id': ObjectId(case_details.get('serviceProvider')) } ) 
            commission_rate = float(service_provider_details.get('commission'))
            application_fee = (commission_rate/100)*total_case_fee
            total_payable_amount = total_case_fee - application_fee
            sp_currency = case_details.get('rate').split(' ')[-1]
            # getting information from stripe account
            stripe_admin_account_info = stripe.Balance.retrieve()
            admin_stripe_available = stripe_admin_account_info.get('available')
            admin_stripe_balance = admin_stripe_available[0].get('amount')
            admin_stripe_currency = admin_stripe_available[0].get('currency')
            return {
                "transfer_info": {
                    "total_case_fee": total_case_fee,
                    "commission_rate": commission_rate,
                    "application_fee": application_fee,
                    "conversion_rate": case_details.get('conversion_rate'),
                    "total_payable_amount": total_payable_amount,
                    "total_payable_amount_converted": total_payable_amount * float(case_details.get('conversion_rate')),
                    "sp_currency": sp_currency,
                    "admin_stripe_balance": admin_stripe_balance,
                    "admin_stripe_currency": admin_stripe_currency,
                    "sp_stripe_account": service_provider_details.get('stripe_account_id')
                }
            }, 200
        return {"message": "case does not exist"}, 404
        # total available stripe balance
        # total case fee
        # application fee , commission rate
        # total amount to be paid
        # currency