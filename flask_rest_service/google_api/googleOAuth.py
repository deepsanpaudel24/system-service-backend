from flask import jsonify, redirect, url_for, redirect, session, request
from flask_restful import Resource
from flask_rest_service import app, api, mongo
from flask_jwt_extended import get_jwt_identity, jwt_required, jwt_optional
from bson.objectid import ObjectId
import json
from bson import json_util
import os
import requests
from datetime import datetime, timedelta



CLIENT_ID = '715950681414-l4h7td0sunglcjc0g44mtf15cudcak31.apps.googleusercontent.com'
CLIENT_SECRET = 'kQV-BoxSPv6NMXYLGYxobzfM'  # Read from a file or environmental variable in a real app
SCOPE = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/drive.readonly'
REDIRECT_URI = 'http://127.0.0.1:5000/api/v1/oauth2callback'


class Authorize(Resource):
    @jwt_optional
    def get(self):
        current_user = get_jwt_identity()
        # for the first time when the user authorize, current_user is not empty 
        if current_user:
            google_credentials = mongo.db.google_credentials.find_one({'userId':ObjectId(current_user)})
        # this is the case which comes from OAuth2CallBack when it redirects after saving the google credentials
        else:
            document = mongo.db.google_credentials.find().sort("_id", -1).limit(1)
            google_credentials = mongo.db.google_credentials.find_one({'userId':ObjectId(document[0]['userId'])})

        if not google_credentials:
            id = mongo.db.google_credentials.insert({
                'userId':ObjectId(current_user)
            })
            return redirect(url_for('oauth2callback'))
    
        credentials = google_credentials['credentials']
        if datetime.now() >= google_credentials['expiretime']:
            return redirect(url_for('oauth2callback'))
        else:
            return redirect('http://localhost:3000/user/profile-setting')
            

class OAuth2CallBack(Resource):
    def get(self):
        if 'code' not in request.args:
            auth_uri = ('https://accounts.google.com/o/oauth2/v2/auth?response_type=code'
                        '&client_id={}&redirect_uri={}&scope={}&access_type=offline& include_granted_scopes=true').format(CLIENT_ID, REDIRECT_URI, SCOPE)
            return {'auth_uri':auth_uri}
        else:
            auth_code = request.args.get('code')
            data = {'code': auth_code,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'grant_type': 'authorization_code'
                    }
            resp = requests.post('https://oauth2.googleapis.com/token', data=data)

            # Now, update the lastest document inserted in the google_credentials with the resp.json()
            # resp.json() is the credentials from google
            document = mongo.db.google_credentials.find().sort("_id", -1).limit(1)
            mongo.db.google_credentials.update_one({'_id': ObjectId(document[0]['_id'])}, {
                    '$set': {
                    'credentials': resp.json(),
                    'refresh_token': resp.json()['refresh_token'],
                    'expiretime': datetime.now() + timedelta(seconds=3000)  
                }
            })
            return redirect(url_for('authorize'))

class Revoke(Resource):
    def get(self):
        if 'credentials' not in session:
            redirect(url_for('authorize'))
        credentials = json.loads(session['credentials'])
        resp=requests.post('https://oauth2.googleapis.com/revoke',params={'token': credentials['access_token']},headers = {'content-type': 'application/x-www-form-urlencoded'})

        status_code = getattr(resp, 'status_code')
        if status_code == 200:
            return jsonify('Credentials successfully revoked.')
        else:
            return jsonify('An error occurred.')

class ClearCredentials(Resource):
    def get(self):
        if 'credentials' in session:
            del session['credentials']
            return jsonify('Credentials have been cleared')
        return jsonify('Not found google credentials')


class GoogleDriveFetchFiles(Resource):
    @jwt_required
    def get(self, folder_name):
        current_user = get_jwt_identity()
        google_credentials = mongo.db.google_credentials.find_one({'userId':ObjectId(current_user)})
        credentials = google_credentials['credentials']
        # refreshing the access token 
        if datetime.now() >= google_credentials['expiretime']:
            data = {
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'grant_type': 'refresh_token',
                    'refresh_token': google_credentials['refresh_token']
                    }
            resp = requests.post('https://oauth2.googleapis.com/token', data=data)
            mongo.db.google_credentials.update_one({'userId': ObjectId(current_user)}, {
                    '$set': {
                    'credentials': resp.json(),
                    'expiretime': datetime.now() + timedelta(seconds=3000)  
                }
            })
            # gets the updated google credentials
            google_credentials = mongo.db.google_credentials.find_one({'userId':ObjectId(current_user)})
            credentials = google_credentials['credentials']

        req_uri = 'https://www.googleapis.com/drive/v3/files'
        headers_for_querying = {'Authorization': 'Bearer {}'.format(credentials['access_token'])}

        # step 1st: querying  if folder exist or not 
        query = {'q': f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"} 
        resp = requests.get(req_uri, headers=headers_for_querying,params=query)
        resp_in_obj=resp.json()
        folder_info = resp_in_obj['files'][0]
        folder_id = folder_info.get('id')
        query2 = {'q': f"'{folder_id}' in parents"} 
        resp2 = requests.get(req_uri, headers=headers_for_querying,params=query2)
        return resp2.json()



class GoogleDriveCreateFile(Resource):
    @jwt_required
    def post(self):
        data = request.get_json()
        file_type = data['file_type']
        folder_name = data['folder_name']
        file_name= data['file_name']
        current_user = get_jwt_identity()
        google_credentials = mongo.db.google_credentials.find_one({'userId':ObjectId(current_user)})
        credentials = google_credentials['credentials']
        # refreshing the access token 
        if datetime.now() >= google_credentials['expiretime']:
            data = {
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'grant_type': 'refresh_token',
                    'refresh_token': google_credentials['refresh_token']
                    }
            resp = requests.post('https://oauth2.googleapis.com/token', data=data)
            mongo.db.google_credentials.update_one({'userId': ObjectId(current_user)}, {
                    '$set': {
                    'credentials': resp.json(),
                    'expiretime': datetime.now() + timedelta(seconds=3000)  
                }
            })
            # gets the updated google credentials
            google_credentials = mongo.db.google_credentials.find_one({'userId':ObjectId(current_user)})
            credentials = google_credentials['credentials']

        req_uri = 'https://www.googleapis.com/drive/v3/files'
        headers_for_querying = {'Authorization': 'Bearer {}'.format(credentials['access_token'])}
        headers_for_creating = {
            'Authorization': 'Bearer {}'.format(credentials['access_token']),
            'Content-Type': 'application/json'
            }

        # step 1st: querying  if folder exist or not 
        query = {'q': f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"} 
        resp = requests.get(req_uri, headers=headers_for_querying,params=query)
        resp_in_obj=resp.json()
        # stet2 : if exist and or not what is folder id will be
        folder_id = "" 
        if resp_in_obj['files']:
            folder_info = resp_in_obj['files'][0]
            folder_id = folder_info.get('id')
        else:
            # if there is not folder then create one and set folder id
            folder_data = {
              'name': folder_name,
              'mimeType': 'application/vnd.google-apps.folder',
            }
            folder_resp = requests.post(req_uri, headers=headers_for_creating, data=json.dumps(folder_data))
            folder_resp_in_obj = folder_resp.json()
            folder_id = folder_resp_in_obj.get('id')
        
        
        #step 3: Creating a file inside the folder according to folder id
        file_metadata = {
                    'name': file_name,
                    'mimeType': f"application/vnd.google-apps.{file_type}",
                    'parents': [folder_id]
            }
        file_resp = requests.post(req_uri, headers=headers_for_creating, data=json.dumps(file_metadata))
        file_resp_in_obj = file_resp.json()
        file_id = file_resp_in_obj.get('id')
        if data['file_type'] == "document":
            redirect_to = f"https://docs.google.com/document/d/{file_id}/edit"
        elif data['file_type'] == "presentation":
            redirect_to = f"https://docs.google.com/presentation/d/{file_id}/edit"
        else:
            redirect_to = f"https://docs.google.com/spreadsheets/d/{file_id}/edit#gid=0"
        return {'redirect_to': redirect_to}