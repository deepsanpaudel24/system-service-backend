from flask_rest_service import app
from flask_rest_service.communication import socketio
import os 

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    socketio.run(app, debug=True)