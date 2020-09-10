import os
from flask import jsonify
from flask_rest_service import app, api, mongo, mail
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import jwt_required, get_jwt_claims, get_jwt_identity
from bson.objectid import ObjectId


_user_parser =  reqparse.RequestParser()

_user_parser.add_argument('user_type',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

_basicProfile_parser = reqparse.RequestParser()

_basicProfile_parser.add_argument('name',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )
_basicProfile_parser.add_argument('address',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )
_basicProfile_parser.add_argument('phone_number',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )
_basicProfile_parser.add_argument('registration_number',
                                type=str,
                                required=False,
                                help="This field cannot be blank."
                            )

_detailedProfile_parser = reqparse.RequestParser()

_detailedProfile_parser.add_argument('service_type',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )
_detailedProfile_parser.add_argument('service_categories',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )


_billingProfile_parser = reqparse.RequestParser()

_billingProfile_parser.add_argument('card_number',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )
_billingProfile_parser.add_argument('expiry_date',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )
_billingProfile_parser.add_argument('cvc',
                                type=str,
                                required=True,
                                help="This field cannot be blank."
                            )

class Profile(Resource):
    @jwt_required
    def get(self):
        claims = get_jwt_claims()
        return {
            "message": "Now user set up profile",
            "user_type": claims['user_type']
        }

class UpdateUserType(Resource):
    @jwt_required
    def put(self):
        data = _user_parser.parse_args()
        claims = get_jwt_claims()
        return {
            "message": "User type received",
            "user_type_old": claims['user_type'],
            "user_type_new": data['user_type']
        }

class UpdateUserProfileBasic(Resource):
    @jwt_required
    def put(self):
        basicData= _basicProfile_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                    '$set': {
                    'name': basicData['name'],
                    'address': basicData['address'],
                    'phone_number': basicData['phone_number'],
                    'registration_number': basicData['registration_number'],
                    'profile_basic_completion':True
                }
            })
            resp = jsonify({
                'profile_basic_completion': True
            })
            return {"profile_basic_completion": True}, 200
        return {
            "message": "User does not exist"
        }, 400

class UpdateUserProfileDetailed(Resource):
    @jwt_required
    def put(self):
        detailedData= _detailedProfile_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                    '$set': {
                    'service_type': detailedData['service_type'],
                    'service_categories': detailedData['service_categories'],
                    'profile_detailed_completion': True
                }
            })
            resp = jsonify({
                'profile_detailed_completion': True
            })
            return {
                "profile_detailed_completion": True,
                "user_type": user.get("user_type")
            }, 200
        return {
            "message": "User does not exist"
        }, 400

class UpdateUserProfileBilling(Resource):
    @jwt_required
    def put(self):
        billingData= _billingProfile_parser.parse_args()
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user:
            mongo.db.users.update_one({'_id': ObjectId(current_user)}, {
                    '$set': {
                    'card_number': billingData['card_number'],
                    'expiry_date': billingData['expiry_date'],
                    'cvc': billingData['cvc'],
                    'profile_billing_completion': True
                }
            })
            resp = jsonify({
                'profile_billing_completion': True
            })
            return {"profile_billing_completion": True}, 200
        return {
            "message": "User does not exist"
        }, 400