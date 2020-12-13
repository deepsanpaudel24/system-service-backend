import os
import stripe
import json
from flask import jsonify
from flask_restful import Resource, request, url_for
from flask_rest_service import app, api, mongo
from datetime import datetime
from flask_rest_service.notifications import InsertNotifications
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

stripe.api_key = os.getenv('STRIPE_API_KEY')
webhook_signing_secret = os.getenv('WEBHOOK_SIGNING_SECRET')

def InsertCheckoutRecords(result):
    metadata = result['metadata']
    if result['mode'] == "subscription":
        id = mongo.db.checkout_transactions.insert ( {
            'clientId': ObjectId(metadata['current_user']),
            'paid_amount': int(result['amount_total']/100),
            'status': "completed",
            'payment_intent_id': result['payment_intent'],
            'mode': result['mode'],
            'received': True,
            'currency': "usd",
            'payment_date': datetime.now().strftime("%B %d, %Y %H:%M:%S")
        } )
    else:
        id = mongo.db.checkout_transactions.insert( {
            'clientId': ObjectId(metadata['clientId']),
            'clientName': metadata['clientName'],
            'caseId': ObjectId(metadata['caseId']),
            'caseTitle': metadata['caseTitle'],
            'paid_amount': int(result['amount_total']/100),
            'due_amount': (float(metadata['total_amount']) - int(result['amount_total'])/100)- float(metadata['advance_amount']),
            'currency': metadata['humanize_currency'],
            'status': "completed",
            'received': True,
            'mode': result['mode'],
            'payment_intent_id': result['payment_intent'],
            'payment_date': datetime.now().strftime("%B %d, %Y %H:%M:%S")
        })

def InsertTransferRecords(result):
    metadata = result['metadata']
    id = mongo.db.checkout_transactions.insert( {
        'serviceProviderId': ObjectId(metadata['spId']),
        'serviceProviderName': metadata['spName'],
        'caseId': ObjectId(metadata['caseId']),
        'caseTitle': metadata['caseTitle'],
        'paid_amount': int(result['amount']/100),
        'currency': result['currency'],
        'conversion_rate': metadata['conversion_rate'],
        'commission_rate': metadata['commission_rate'],
        'application_fee': metadata['application_fee'],
        'transfer_id': result['id'],
        'received': False,
        'mode': "payment",
        'status': "completed",
        'payment_date': datetime.now().strftime("%B %d, %Y %H:%M:%S")
    })
# function to update the case status to on-progress if it is Awaiting-Advance-Payment
def UpdateCaseStatus(result):
    metadata = result['metadata']
    case_details = mongo.db.cases.find_one ( { '_id': ObjectId(metadata['caseId']) } )
    if case_details.get('status') == "Awaiting-Advance-Payment":
        mongo.db.cases.update_one({'_id': ObjectId(metadata['caseId']) }, {
                    '$set': {
                    'status': "On-progress"
                }
            })
    elif case_details.get('status') == "Confirm-Completion":
        mongo.db.cases.update_one({'_id': ObjectId(metadata['caseId']) }, {
                    '$set': {
                    'status': "Client-Final-Installment-Paid"
                }
            })


# function to update the case status to Closed if it is Client-Final-Installment-Paid
def UpdateCaseToClosed(result):
    metadata = result['metadata']
    case_details = mongo.db.cases.find_one ( { '_id': ObjectId(metadata['caseId']) } )
    mongo.db.cases.update_one({'_id': ObjectId(metadata['caseId']) }, {
                '$set': {
                'status': "Closed"
            }
        })

# function to update the case status to on-progress if it is Awaiting-Advance-Payment
def UpdateTransferStatusReversed(result):
    metadata = result['metadata']
    transfer_details = mongo.db.transfer_transactions.find_one ( { 'transfer_id': result['id'] } )
    mongo.db.transfer_transactions.update_one( {'transfer_id': result['id'] }, {
                '$set': {
                'status': "Reversed"
            }
        })

# function to update the case status to on-progress if it is Awaiting-Advance-Payment
def UpdateTransferStatusPaid(result):
    metadata = result['metadata']
    transfer_details = mongo.db.transfer_transactions.find_one ( { 'transfer_id': result['id'] } )
    mongo.db.transfer_transactions.update_one( {'transfer_id': result['id'] }, {
                '$set': {
                'status': "Paid",
                'transfer_paid_date': datetime.now().strftime("%B %d, %Y %H:%M:%S")
            }
        })

# function to update the expiry date of the user
def UpdateExpiryDate(current_user, subscribe_type):
    # If the user has child accounts, gotta update their expiry dates as well...
    user_details = mongo.db.users.find_one( { '_id' : ObjectId(current_user)} )
    expiry_date = user_details.get('expiryDate')
    #expiryDate = createdDate + timedelta(days=(1*7)) 
    if subscribe_type == "monthly":
        new_expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d') + timedelta(days=(1*30))
    else: 
        new_expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d') + timedelta(days=(1*365)) 
    mongo.db.users.update_one( {'_id': ObjectId(current_user) }, {
                '$set': {
                'expiryDate': new_expiry_date.strftime('%Y-%m-%d')
            }
        })

    mongo.db.users.update( {'owner': ObjectId(current_user) }, {
                '$set': {
                'expiryDate': new_expiry_date.strftime('%Y-%m-%d')
            }
        })

class Webhook(Resource):
    def post(self):
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get("Stripe-Signature")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_signing_secret
            )

        except ValueError as e:
            # Invalid payload
            return "Invalid payload", 400
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return "Invalid signature", 400

        # Handle the checkout.session.completed event
        if event["type"] == "checkout.session.completed":
            result = event['data']['object']
            metadata = result['metadata']

            # the mode of payment is subscription if the user is doing checkout for their subscription
            if result['mode'] == "subscription":
                current_user = metadata['current_user']
                subscribe_type = metadata['subscribe_type']

                # Needs to update the user's employee account as well
                UpdateExpiryDate(current_user, subscribe_type)
                # Insert the record of subscription payments in the database 
                InsertCheckoutRecords(result)
            else:
                # step1: insert transactions record in database collection checkout_transactions
                InsertCheckoutRecords(result)

                # step2: Notify super admin about the payment received from client
                notification_values = {
                    "title" : f"{result['amount_total']/100} {metadata['humanize_currency']} received from {metadata['clientName']}",
                    "sender": metadata['clientId'],
                    "receiver": ObjectId("5f7196d7be625540246db3d7"),
                    "link": f"/sadmin/case/{metadata['caseId']}"
                } 
                InsertNotifications(**notification_values)

                # step3: Notify Service Provider about the payment received by super admin from client
                notification_values_sp = {
                    "title" : f"{result['amount_total']/100} {metadata['humanize_currency']} received from {metadata['clientName']} by super admin.",
                    "sender": metadata['clientId'],
                    "receiver": ObjectId(metadata['serviceProviderId']),
                    "link": f"/user/case/{metadata['caseId']}"
                } 
                InsertNotifications(**notification_values_sp) 

                # Step4: If this is advance installment update the case to On-progress else update the case to Client-Final-Installment-Paid
                # Update the case status to On-progress from Awaiting-Advance-Payment
                UpdateCaseStatus(result)
        
        # Handle event after the transfer has been created
        elif event["type"] == "transfer.created":
            result = event['data']['object']
            metadata = result['metadata']
            # step1: insert transactions record in database collection transfer_transactions
            InsertTransferRecords(result)
            # step2: Notify the service provider about the payment received from super admin for the case
            notification_values = {
                "title" : f"{result['amount']/100} usd received from super admin.",
                "sender": ObjectId("5f7196d7be625540246db3d7"),
                "receiver": ObjectId(metadata['spId']),
                "link": f"/user/case/{metadata['caseId']}"
            } 
            InsertNotifications(**notification_values)

            # step4: Update the case status to Closed from Client-Final-Installment-Paid
            UpdateCaseToClosed(result)
        
        # Handle event after the transfer has been paid 
        # Not transfer.paid because 
        elif event["type"] == "payout.paid":
            result = event['data']['object']
            UpdateTransferStatusPaid(result)
        
        # Handle event after the transfer failed
        elif event["type"] == "payout.failed":
            result = event['data']['object']
            print('result from webhook of transfer failed', result)
        
        # Handle event after the transfer failed
        elif event["type"] == "transfer.reversed":
            result = event['data']['object']
            UpdateTransferStatusReversed(result)

        else:
            # Unexpected event type
            print('Unhandled event type {}'.format(event['type']))
        return jsonify(success=True)