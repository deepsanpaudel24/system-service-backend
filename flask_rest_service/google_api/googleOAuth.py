from flask import jsonify, redirect, url_for, redirect, session, request
from flask_restful import Resource
from flask_rest_service import app, api, mongo
#from main import app, api, mongo, mail
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson.objectid import ObjectId
import json
from bson import json_util
import os
import requests

import googleapiclient.discovery
import google_auth_oauthlib.flow
import google.oauth2.credentials


# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive.readonly',
          'https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/spreadsheets.readonly']

API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


class TestGoogleApi(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        google_credentials = mongo.db.google_credentials.find_one({"userId" : ObjectId(current_user)})
        if not google_credentials:
            return redirect('authorize')

        # Load credentials from the session.
        credentials = google.oauth2.credentials.Credentials(
            **google_credentials.get('credentials'))

        drive = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

        files = drive.files().list().execute()

        # Save credentials back to session in case access token was refreshed.
        # ACTION ITEM: In a production app, you likely want to save these
        #              credentials in a persistent database instead.
        #session['credentials'] = credentials_to_dict(credentials)
        mongo.db.google_credentials.update_one({"userId" : ObjectId(current_user)}, {
                    '$set': {
                    'credentials': credentials_to_dict(credentials)
                }
            })

        return jsonify(**files)


class Authorize(Resource):
    @jwt_required
    def get(self):
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES)

        # The URI created here must exactly match one of the authorized redirect URIs
        # for the OAuth 2.0 client, which you configured in the API Console. If this
        # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
        # error.
        flow.redirect_uri = url_for('oauth2callback', _external=True)

        authorization_url, state = flow.authorization_url(
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for web server apps.
            access_type='offline',
            # Enable incremental authorization. Recommended as a best practice.
            include_granted_scopes='true')

        # Store the state so the callback can verify the auth server response.
        session['state'] = state

        return redirect(authorization_url)


class OAuth2CallBack(Resource):
    @jwt_required
    def get(self):
        # Specify the state when creating the flow in the callback so that it can
        # verified in the authorization server response.
        state = session['state']

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
        flow.redirect_uri = url_for('oauth2callback', _external=True)

        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials in the session.
        # ACTION ITEM: In a production app, you likely want to save these
        #              credentials in a persistent database instead.
        credentials = flow.credentials
        current_user = get_jwt_identity()
        # insert these credentials in database
        id = mongo.db.google_credentials.insert({
            "userId": ObjectId(current_user),
            "credentials" : credentials_to_dict(credentials)
        })
        #session['credentials'] = credentials_to_dict(credentials)

        return redirect(url_for('testgoogleapi'))


class Revoke(Resource):
    def get(self):
        google_credentials = mongo.db.google_credentials.find_one({"userId" : "client1"})
        if not google_credentials:
            return jsonify('You need to authorizebefore ' +
                           'testing the code to revoke credentials.')

        credentials = google.oauth2.credentials.Credentials(
            **google_credentials.get('credentials'))

        revoke = requests.post('https://oauth2.googleapis.com/revoke',
                               params={'token': credentials.token},
                               headers={'content-type': 'application/x-www-form-urlencoded'})

        status_code = getattr(revoke, 'status_code')
        if status_code == 200:
            return jsonify('Credentials successfully revoked.')
        else:
            return jsonify('An error occurred.')


class ClearCredentials(Resource):
    def get(self):
        google_credentials = mongo.db.google_credentials.find_one({"userId" : "client1"})
        if google_credentials:
            delete_credentials = mongo.db.google_credentials.remove({'userId': "client1"})
            return {"message": "Credentials have been cleared."}, 200
        return {"message": "Google credentials not found"}


class MakeSpreadsheets(Resource):
    def get(self):
        google_credentials = mongo.db.google_credentials.find_one({"userId" : "client1"})
        if not google_credentials:
            return redirect('authorize')

        credentials = google.oauth2.credentials.Credentials(
            **google_credentials.get('credentials'))

        sheet_service = googleapiclient.discovery.build(
            'sheets', 'v4', credentials=credentials)
        spreadsheet = {
            'properties': {
                'title': "freefire4"
            }
        }
        spreadsheet = sheet_service.spreadsheets().create(body=spreadsheet,
                                                          fields='spreadsheetId').execute()
        return redirect(f"https://docs.google.com/spreadsheets/d/{spreadsheet.get('spreadsheetId')}/edit#gid=0")


class MakeDocs(Resource):
    def get(self):
        google_credentials = mongo.db.google_credentials.find_one({"userId" : "client1"})
        if not google_credentials:
            return redirect('authorize')

        credentials = google.oauth2.credentials.Credentials(
            **google_credentials.get('credentials'))

        title = 'damaulihahah'
        doc_service = googleapiclient.discovery.build(
            'docs', 'v1', credentials=credentials)
        body = {
            'title': title
        }
        doc = doc_service.documents() \
            .create(body=body).execute()

        return redirect(f"https://docs.google.com/document/d/{doc.get('documentId')}/edit")


class MakeSlides(Resource):
    def get(self):
        google_credentials = mongo.db.google_credentials.find_one({"userId" : "client1"})
        if not google_credentials:
            return redirect('authorize')

        credentials = google.oauth2.credentials.Credentials(
            **google_credentials.get('credentials'))

        title = 'myslide'
        slides_service = googleapiclient.discovery.build(
            'slides', 'v1', credentials=credentials)
        body = {
            'title': title
        }
        presentation = slides_service.presentations() \
            .create(body=body).execute()

        return redirect(f"https://docs.google.com/presentation/d/{presentation.get('presentationId')}/edit")


class MakeFileInsideFolder(Resource):
    def get(self):
        # Create a folder
        google_credentials = mongo.db.google_credentials.find_one({"userId" : "client1"})
        if not google_credentials:
            return redirect('authorize')

        credentials = google.oauth2.credentials.Credentials(
            **google_credentials.get('credentials'))

        drive_service = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

        file_metadata = {
            'name': 'Hometown',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=file_metadata,
                                              fields='id').execute()
        # Create a file in a folder
        folder_id = folder.get('id')

        # 'mimeType': 'application/vnd.google-apps.spreadsheet'
        # 'mimeType': 'application/vnd.google-apps.document'
        # 'mimeType': 'application/vnd.google-apps.presentation'

        file_metadata = {
            'name': 'MyhomeTown',
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]
        }
        file = drive_service.files().create(body=file_metadata,
                                            fields='id').execute()
        print('File ID: %s' % file.get('id'))
        return jsonify(file)
