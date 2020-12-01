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

# Set your secret key. Remember to switch to your live secret key in production!
# See your keys here: https://dashboard.stripe.com/account/apikeys

stripe.api_key = 'sk_test_51HrMHgE8BAcK1TWiC1rrReLpfQm05TZvk5c0hfIlnuVZp2sTp78CANnR6QTfz3snvPHXlEfZKwc7gyzBkW0sX1CP00uNx2v3X2'
webhook_signing_secret = 'whsec_eSTZV9YteFfUv1inEile2LRE5xlg6quk'

def InsertCheckoutRecords(result):
    metadata = result['metadata']
    id = mongo.db.checkout_transactions.insert( {
        'clientId': ObjectId(metadata['clientId']),
        'clientName': metadata['clientName'],
        'caseId': ObjectId(metadata['caseId']),
        'caseTitle': metadata['caseTitle'],
        'paid_amount': int(result['amount_total']/100),
        'due_amount': float(metadata['total_amount']) - int(result['amount_total'])/100,
        'currency': metadata['humanize_currency'],
        'status': "completed",
        'payment_intent_id': result['payment_intent'],
        'payment_date': datetime.now().strftime("%B %d, %Y %H:%M:%S")
    })

def InsertTransferRecords(result):
    metadata = result['metadata']
    id = mongo.db.transfer_transactions.insert( {
        'serviceProviderId': ObjectId(metadata['spId']),
        'serviceProviderName': metadata['spName'],
        'caseId': ObjectId(metadata['caseId']),
        'caseTitle': metadata['caseTitle'],
        'paid_amount': int(result['amount']/100),
        'currency': result['currency'],
        'transfer_id': result['id'],
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
    if case_details.get('status') == "Client-Final-Installment-Paid":
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
def UpdateExpiryDate(current_user):
    user_details = mongo.db.users.find_one( { '_id' : ObjectId(current_user)} )
    expiry_date = user_details.get('expiryDate')
    #expiryDate = createdDate + timedelta(days=(1*7)) 
    new_expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d') + timedelta(days=(1*365)) 
    mongo.db.users.update_one( {'_id': ObjectId(current_user) }, {
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
            if result['mode'] == "subscription":
                current_user = metadata['current_user']
                UpdateExpiryDate(current_user)
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