from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
import requests
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime
import os
import werkzeug
from werkzeug.utils import secure_filename
import uuid
from flask_rest_service.notifications import InsertNotifications

_parse = reqparse.RequestParser()

_replyCaseRequest_parser =  reqparse.RequestParser()

_replyCaseRequest_parser.add_argument('title',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_replyCaseRequest_parser.add_argument('desc',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_replyCaseRequest_parser.add_argument('rateType',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_replyCaseRequest_parser.add_argument('rate',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_replyCaseRequest_parser.add_argument('averageTimeTaken',
                    type=int,
                    required=True,
                    help="This field cannot be blank. Please enter your average time taken in hours."
                    )
_replyCaseRequest_parser.add_argument('spDeadline',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_replyCaseRequest_parser.add_argument('paymentType',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )
_replyCaseRequest_parser.add_argument('advancePayment',
                    type=float,
                    required=False,
                    help="This field cannot be blank."
                    )


_acceptProposal_parser =  reqparse.RequestParser()

_acceptProposal_parser.add_argument('accepted',
                    type=str,
                    required=True,
                    help="This field cannot be blank."
                    )

class ReplyCaseRequest(Resource):
    @jwt_required
    def post(self, caseId):
        current_user = get_jwt_identity()
        data = _replyCaseRequest_parser.parse_args()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        case_details = mongo.db.cases.find_one({'_id': ObjectId(caseId)})

        myFiles = request.files
        for key in myFiles:
            _parse.add_argument(
                key, type=werkzeug.datastructures.FileStorage, location='files')
        args = _parse.parse_args()
        filesLocationList = []
        for key in myFiles:
            file = args[key]
            filename = secure_filename(file.filename)
            filename, extension = filename.split('.')
            filename = f"{filename}-{uuid.uuid4().hex}.{extension}"
            dirToSaveFile = '/'.join(app.config['UPLOAD_FOLDER'].split('/')[1:])
            filesLocationList.append(f"{dirToSaveFile}/{filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        

        # get the currency conversion rate and then store it in the proposal details.
        sp_base_currency = data['rate'].split(' ')[-1]
        if sp_base_currency == "pound":
            base_currency = "gbp"
            key="GBPUSD"
            params1 = {"pairs" : "GBPUSD"}
            params2 = {"base" : "GBP", "symbols": "USD"}
        elif sp_base_currency == "euro":
            base_currency = "eur"
            key="EURUSD"
            params1 = {"pairs" : "EURUSD"}
            params2 = {"base" : "EUR", "symbols": "USD"}
        else :
            base_currency = "usd"
            key="USDUSD"
            params1 = {"pairs" : "USDUSD"}
            params2 = {"base" : "USD", "symbols": "USD"}

        # Sending get request to get the conversion rate
        resp1 = requests.get('https://www.freeforexapi.com/api/live', params=params1)
        conversion_rate = resp1.json()['rates'][key]['rate']
        if resp1.status_code != 200:
            resp2 = requests.get('https://api.exchangerate.host/latest', params=params2)
            conversion_rate = resp2.json()['rates']['USD']
        
        if user.get('user_type') == "SPCAe":
            user_owner = mongo.db.users.find_one({'_id': ObjectId(user.get('owner'))})
            id = mongo.db.proposals.insert({
                'title': data['title'],
                'desc': data['desc'],
                'rateType': data['rateType'],
                'rate': data['rate'],
                'averageTimeTaken': data['averageTimeTaken'],
                'spDeadline': data['spDeadline'],
                'caseId': ObjectId(caseId),
                'serviceProvider': ObjectId(user.get('owner')),
                'serviceProvidername': user_owner.get('name'),
                'paymentType': data['paymentType'],
                'advancePayment': data['advancePayment'],
                'conversion_rate': conversion_rate,
                'files': filesLocationList,
                'sentDate': datetime.today().strftime('%Y-%m-%d')
            })                           # insert the data in the collection proposals  
        else:
            id = mongo.db.proposals.insert({
                'title': data['title'],
                'desc': data['desc'],
                'rateType': data['rateType'],
                'rate': data['rate'],
                'averageTimeTaken': data['averageTimeTaken'],
                'spDeadline': data['spDeadline'],
                'caseId': ObjectId(caseId),
                'serviceProvider': ObjectId(current_user),
                'serviceProvidername': user.get('name'),
                'paymentType': data['paymentType'],
                'advancePayment': data['advancePayment'],
                'conversion_rate': conversion_rate,
                'files': filesLocationList,
                'sentDate': datetime.today().strftime('%Y-%m-%d')
            })                           # insert the data in the collection proposals   
        mongo.db.cases.update_one({'_id': ObjectId(caseId)}, {
                    '$set': {
                    'status': "Proposal-Forwarded"
                }
            }) 

        # Send notifiations to the service providers with the message saying they received the case from super admin. 
        notification_values = {
            "title" : f"{user.get('name')} has sent a proposal for your case",
            "sender": ObjectId(current_user),
            "receiver": case_details.get('client'),
            "link": f"/user/case/{caseId}"
        } 
        InsertNotifications(**notification_values)

        return {"message": "Proposal sent successfully"}, 201
    
    @jwt_required
    def get(self, caseId):
        current_user = get_jwt_identity()
        proposal_check_point1 = mongo.db.proposals.find({"$and": [{"serviceProvider": ObjectId(current_user)}, {"caseId": ObjectId(caseId)}]}).sort("_id", -1)
        if proposal_check_point1:
            return {"message": "Sent"}, 200
        return {"message" : "Notsent"}, 404

class CaseProposals(Resource):
    @jwt_required
    def get(self, caseId):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "CCA" or user.get('user_type') == "SA" or user.get('user_type') == "CCAe" or user.get('user_type') == "SAe":
            case = mongo.db.cases.find_one({'_id': ObjectId(caseId)})
            if case:
                proposals = []
                for proposal in mongo.db.proposals.find({'caseId': ObjectId(caseId)}).sort("_id", -1):
                    proposals.append(proposal)
                return json.loads(json.dumps(proposals, default=json_util.default))
            return {
                "message": "The case does not exist any longer"
            }
        return {
            "message": "You are not authorized to view cases"
        }, 403

    
class PropsalDetails(Resource):
    @jwt_required
    def get(self, proposalId):
        propsal = mongo.db.proposals.find_one({'_id': ObjectId(proposalId)})
        if propsal:
            return json.loads(json.dumps(propsal, default=json_util.default))
        return {"message" : "No proposal details"}, 404
    
    @jwt_required
    def put(self, proposalId):
        data = _acceptProposal_parser.parse_args()
        proposal = mongo.db.proposals.find_one({'_id': ObjectId(proposalId)})
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "CCA" or user.get('user_type') == "CCAe":
            accepted_value = False
            status_value = "Declined"
            if data['accepted'] == 'true':
                accepted_value = True
                status_value = "Accepted"
            mongo.db.proposals.update_one({'_id': ObjectId(proposalId)}, {
                '$set': {
                    'accepted': accepted_value,
                    'status': status_value
                }
            })
            if accepted_value == True:
                # advancePayment is the amount of percentage of advance payment of total amount 
                
                mongo.db.cases.update_one({'_id': ObjectId(proposal.get('caseId'))}, {
                    '$set': {
                        'serviceProvider': ObjectId(proposal.get('serviceProvider')),
                        'serviceProvidername': proposal.get('serviceProvidername'),
                        'averageTimeTaken': proposal.get('averageTimeTaken'),
                        'spDeadline': proposal.get('spDeadline'),
                        'status': "Contract-Waiting",
                        'rateType': proposal.get('rateType'),
                        'rate': proposal.get('rate'),
                        'paymentType':proposal.get('paymentType'),
                        'advancePayment':proposal.get('advancePayment'),
                        'conversion_rate': proposal.get('conversion_rate')
                    }
                })
                # Send notifiations to the service providers with the message saying their proposal has been accepted
                notification_values = {
                    "title" : f"Your proposal has been accepted by the client {user.get('name')} ",
                    "sender": ObjectId(current_user),
                    "receiver": ObjectId(proposal.get('serviceProvider')),
                    "link": f"/user/case/{ObjectId(proposal.get('caseId'))}"
                } 
                InsertNotifications(**notification_values)

                # Now after this proposal has been accepted, the others proposal should be auto declined. 
                # Declining a proposal means, other all proposals for this case has be be set declined in their status and
                # the other service providers to whom this case was forwarded by super admin 
                # except the one whose proposal got accepted should be notified that the client has accepted some other service providers 
                # proposal.
                mongo.db.proposals.update( { "$and": [ {'caseId': ObjectId(proposal.get('caseId') ) }, { '_id' : { "$ne": ObjectId(proposalId) } } ] }, {
                    '$set': {
                        'accepted': False,
                        'status': "Declined"
                    }
                })

                case_details = mongo.db.cases.find_one ( { '_id': ObjectId( proposal.get('caseId') ) } )

                forwarded_service_providers = case_details.get('forwardTo')
                for sp in forwarded_service_providers:
                    if sp == proposal.get('serviceProvider'):
                        print("Avoid this service provider with id", proposal.get('serviceProvider'))
                    else:
                        # Send notifiations to the service providers with the message saying their proposal has been accepted
                        notification_values = {
                            "title" : f"Your proposal has been declined for the case {case_details.get('title')}",
                            "sender": ObjectId(current_user),
                            "receiver": ObjectId(sp),
                            "link": f"/user/cases"
                        } 
                        InsertNotifications(**notification_values)

            return {"message": accepted_value}
        return {
            "message": "You are not authorized to take action"
        }, 403

class ProposalDetailsForSP(Resource):
    @jwt_required
    def get(self, caseId):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "SPCAe":
            proposal = mongo.db.proposals.find_one({'caseId': ObjectId(caseId), 'serviceProvider': ObjectId(user.get('owner'))})
        else:
            proposal = mongo.db.proposals.find_one({'caseId': ObjectId(caseId), 'serviceProvider': ObjectId(current_user)})
        if proposal:
            return json.loads(json.dumps(proposal, default=json_util.default))
        return {"message" : "No proposal details"}, 404
                