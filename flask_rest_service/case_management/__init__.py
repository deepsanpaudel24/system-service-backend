from flask_rest_service.case_management.newCase_request import AddNewCaseRequest, UpdateRelatedDocuments, DeleteRelatedDocuments
from flask_rest_service.case_management.cases import( Cases, ClientCasesDetails, ServiceProviderCasesActive, 
                                                        ForwardCaseRequest, ServiceProviderCasesDetails, UndoCaseForward
                                                    )
from flask_rest_service.case_management.service_provider_cases import ServiceProviderCases
from flask_rest_service.case_management.client_cases import ClientCases
from flask_rest_service.case_management.employee_cases import EmployeeCases
from flask_rest_service.case_management.employee_cases_for_sp import EmployeeCasesForSP
from flask_rest_service.case_management.case_request_reply import ReplyCaseRequest, CaseProposals, PropsalDetails, ProposalDetailsForSP
from flask_rest_service.case_management.assign_case import EmployeeCaseAssignment
from flask_rest_service.case_management.contract_paper import UploadContractPaper, ContractDetails, ConfirmContractPaper