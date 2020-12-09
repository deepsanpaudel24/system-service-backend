import json
import os

import stripe
#from dotenv import load_dotenv, find_dotenv
from flask import jsonify, redirect, request, session
from flask_restful import Resource, request, url_for
from flask_rest_service import app, api, mongo
from bson.objectid import ObjectId
from flask_jwt_extended import get_jwt_identity, jwt_required

# Setup Stripe python client library
# load_dotenv(find_dotenv())
# stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = 'sk_test_51HrMHgE8BAcK1TWiC1rrReLpfQm05TZvk5c0hfIlnuVZp2sTp78CANnR6QTfz3snvPHXlEfZKwc7gyzBkW0sX1CP00uNx2v3X2'


def _generate_account_link(account_id, origin):
    account_link = stripe.AccountLink.create(
        type='account_onboarding',
        account=account_id,
        refresh_url=f"{app.config['FRONTEND_DOMAIN']}/api/v1/onboard-user/refresh",
        return_url=f"{app.config['FRONTEND_DOMAIN']}/user/home",
    )
    return account_link.url

# update stripe id in the users documents for service providers
def UpdateStripeAccountId(accountId, current_user):
    mongo.db.users.update_one({'_id': ObjectId(current_user) }, {
                                '$set': {
                                    'stripe_account_id': accountId
                                }
                            })


class Onboard_user(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        account = stripe.Account.create(type='express')
        UpdateStripeAccountId(account.id, current_user)
        # Store the account ID.
        session['account_id'] = account.id

        origin = request.headers['origin']
        account_link_url = _generate_account_link(account.id, origin)
        try:
            return jsonify({'url': account_link_url})
        except Exception as e:
            return jsonify(error=str(e)), 403


class Onboard_user_refresh(Resource):
    def get(self):
        if 'account_id' not in session:
            return redirect(f"{app.config['FRONTEND_DOMAIN']}/user/home")

        account_id = session['account_id']

        origin = ('https://' if request.is_secure else 'http://') + \
            request.headers['host']
        account_link_url = _generate_account_link(account_id, origin)
        return redirect(account_link_url)


class UserStripeAccInfo(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id':ObjectId(current_user)})
        if user.get('stripe_account_id') is not None:
            stripe_acc_id = user.get('stripe_account_id')
            resp = stripe.Account.retrieve(stripe_acc_id)

            if not resp.get('details_submitted'):
                account_link_url = _generate_account_link(stripe_acc_id)
                try:
                    resp['url']=account_link_url
                    return resp
                except Exception as e:
                    return jsonify(error=str(e)), 403

            return resp
        return jsonify({'showOnboard':True})

# to let the super admin know if the service provider can receive the payment
class SPStripeAccInfo(Resource):
    @jwt_required
    def get(self, spId):
        user = mongo.db.users.find_one({'_id':ObjectId(spId)})
        if user.get('stripe_account_id') is not None:
            stripe_acc_id = user.get('stripe_account_id')
            resp = stripe.Account.retrieve(stripe_acc_id)

            if not resp.get('details_submitted'):
                return {"message": "Service Providers has not submitted all the required information to accept payment."}, 400

            return resp, 200
        return {"message": "Service providers has not onboarded on stripe yet." }, 404

