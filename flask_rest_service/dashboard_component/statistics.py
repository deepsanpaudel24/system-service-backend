from flask import jsonify
from flask_rest_service import app, api, mongo
from flask_restful import Resource, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util

class ServiceProviderStats(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one( { '_id': ObjectId(current_user ) } )
        if user.get('user_type') == "SPCA":
            # step1: Find the total number of cases
            number_cases = mongo.db.cases.find({'serviceProvider': ObjectId(current_user)}).count()
            # step2: Find the total number of employees
            number_employees = mongo.db.users.find( { 'owner': ObjectId(current_user) } ).count()
            # step3: Find the total number of services
            number_services = mongo.db.services.find( { 'serviceOwner': ObjectId(current_user) } ).count()
            # step4: Find the total number of Clients
            number_clients = mongo.db.users.find( { 'invited_by': ObjectId(current_user) } ).count()
            # step5: Find the total number of tasks
            number_tasks = mongo.db.custom_tasks.find( { 'workBy': ObjectId(current_user)  } ).count()
            # step6: Find the total number of Intake Forms
            number_forms = mongo.db.intake_forms.find( { 'createdBy' : ObjectId(current_user) } ).count()
            return {
                "total_no_cases": number_cases,
                "total_no_employees": number_employees,
                "total_no_services": number_services,
                "total_no_clients": number_clients,
                "total_no_tasks": number_tasks,
                "total_no_forms": number_forms
            },200
        return {"message": "You are not allowed to access this endpoint"}

class ClientStats(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one( { '_id': ObjectId(current_user ) } )
        if user.get('user_type') == "CCA":
            # step1: Find the total number of cases
            number_cases = mongo.db.cases.find({'client': ObjectId(current_user)}).count()
            # step2: Find the total number of employees
            number_employees = mongo.db.users.find( { 'owner': ObjectId(current_user) } ).count()
            # step3: Find the total number of closed cases
            number_closed_cases = mongo.db.cases.find( { "$and" : [ {'client': ObjectId(current_user)} , {'status': "Closed" } ] } ).count()
            return {
                "total_no_cases": number_cases,
                "total_no_employees": number_employees,
                "total_no_closed_cases": number_closed_cases
            }, 200
        return {"message": "You are not allowed to access this endpoint"}

class SuperadminStats(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one( { '_id': ObjectId(current_user ) } )
        if user.get('user_type') == "SA":
            # step1: Find the total number of cases
            number_cases = mongo.db.cases.find().count()
            # step2: Find the total number of employees
            number_employees = mongo.db.users.find( { 'owner': ObjectId(current_user) } ).count()
            # step3: Find the total number of closed cases
            number_closed_cases = mongo.db.cases.find(  {'status': "Closed" } ).count()
            # step4: Find the total number of users in the system
            number_users = mongo.db.users.find( ).count()
            # step5: Find the total number of tasks
            number_active_users = mongo.db.users.find( { 'is_verified': True  } ).count()
            # step6: Find the total number of closed cases
            number_onprogress_cases = mongo.db.cases.find(  {'status': 'On-progress' } ).count()
            return {
                "total_no_cases": number_cases,
                "total_no_employees": number_employees,
                "total_no_closed_cases": number_closed_cases,
                "total_no_users": number_users,
                "total_no_active_users": number_active_users,
                "total_onprogress_cases": number_onprogress_cases
            },200
        return {"message": "You are not allowed to access this endpoint"}