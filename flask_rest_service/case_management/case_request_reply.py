from flask_rest_service import app, api, mongo
from flask_restful import Resource, request, reqparse, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
from datetime import datetime


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
                    type=float,
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
            'sentDate': datetime.today().strftime('%Y-%m-%d')
        })                           # insert the data in the collection proposals   
        mongo.db.cases.update_one({'_id': ObjectId(caseId)}, {
                    '$set': {
                    'status': "Proposal-Forwarded"
                }
            })                                                                                         
        return {"message": "Proposal sent successfully"}, 201
    
    @jwt_required
    def get(self, caseId):
        current_user = get_jwt_identity()
        proposal_check_point1 = mongo.db.proposals.find({"$and": [{"serviceProvider": ObjectId(current_user)}, {"caseId": ObjectId(caseId)}]})
        if proposal_check_point1:
            return {"message": "Sent"}, 200
        return {"message" : "Notsent"}, 404

class CaseProposals(Resource):
    @jwt_required
    def get(self, caseId):
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({'_id': ObjectId(current_user)})
        if user.get('user_type') == "CCA" or user.get('user_type') == "CS" or user.get('user_type') == "SA":
            case = mongo.db.cases.find_one({'_id': ObjectId(caseId)})
            if case:
                proposals = []
                for proposal in mongo.db.proposals.find({'caseId': ObjectId(caseId)}):
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
        if user.get('user_type') == "CCA" or user.get('user_type') == "CS":
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
                mongo.db.cases.update_one({'_id': ObjectId(proposal.get('caseId'))}, {
                    '$set': {
                        'serviceProvider': ObjectId(proposal.get('serviceProvider')),
                        'serviceProvidername': proposal.get('serviceProvidername'),
                        'status': "On-progress",
                        'rateType': proposal.get('rateType'),
                        'rate': proposal.get('rate')
                    }
                })
            return {"message": accepted_value}
        return {
            "message": "You are not authorized to take action"
        }, 403
                