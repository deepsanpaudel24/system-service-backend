from flask_rest_service.case_management.newCase_request import AddNewCaseRequest
from flask_rest_service.case_management.cases import( Cases, ClientCases, ClientCasesDetails, ServiceProviderCasesActive, 
                                                        ForwardCaseRequest, ServiceProviderCases, ServiceProviderCasesDetails,
                                                        EmployeeCases
                                                    )
from flask_rest_service.case_management.case_request_reply import ReplyCaseRequest, CaseProposals, PropsalDetails, ProposalDetailsForSP
from flask_rest_service.case_management.assign_case import EmployeeCaseAssignment
from flask_rest_service.case_management.contract_paper import UploadContractPaper, ContractDetails, ConfirmContractPaper