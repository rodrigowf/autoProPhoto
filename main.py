# -*- coding: utf-8 -*-

# [START gae_python37_app]
import flask
import requests
from flask_cors import CORS, cross_origin
from flask_session import Session

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from drive_process import ProcessThread


drive_redirect = 'http://refoto.appspot.com/drive'

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "./client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata', 'https://www.googleapis.com/auth/drive']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

app = flask.Flask(__name__)
app.secret_key = b'5oZW6\n$#^#3w3FE3'

# Session config
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

# CORS - cross domain config
cors = CORS(app, supports_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'


def addHeaders(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add("Access-Control-Allow-Headers", "Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, PATCH, DELETE")
    response.headers.add("Content-Type", "application/json;charset=UTF-8")
    return response


class RunningStatus:
    def __init__(self):
        self.running = False
        self.folder_name = ''
        self.files_list = []
        self.current_file = 0
        self.progress = 0
        self.my_thread_id = 0
        self.cancel_signal = False


@app.route('/')
def index():
    return print_index_table()


@app.route('/filelist')
def get_fileslist():
    if 'status' not in flask.session:
        return flask.jsonify({'running': 'False'})

    status = flask.session['status']

    response = flask.jsonify({'running': 'True',
                              'folder_name': status.folder_name,
                              'files_list': status.files_list})
    return addHeaders(response)


@app.route('/status')
def get_status():
    if 'status' not in flask.session:
        return flask.jsonify({'running': 'False'})

    status = flask.session['status']

    if not status.running:
        flask.session.pop('status', None)
        return flask.jsonify({'running': 'False'})

    response = flask.jsonify({'running': 'True',
                              'current_file': status.current_file,
                              'progress': status.progress})
    return addHeaders(response)


@app.route('/cancel')
def cancel_processing():
    if 'status' not in flask.session:
        return flask.jsonify({'running': 'False'})

    status = flask.session['status']
    status.cancel_signal = True
    ProcessThread.threads[status.my_thread_id].join()
    del status
    flask.session.pop('status', None)
    response = flask.jsonify({'running': 'False',
                              'done': 'True'})
    return addHeaders(response)


@app.route('/process_folder/<folder_id>')
def process_folder(folder_id):
    # Check if it's logged in, if not, do it.
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    if 'status' in flask.session and flask.session['status'].running is True:
        return addHeaders(flask.jsonify({'running': 'True'}))

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

    status = RunningStatus()
    flask.session['status'] = status

    # Create and start the thread that process all the selected folder
    thread = ProcessThread(credentials, folder_id, status)
    thread.start() # aqui q ele faz status.running = True


    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    return addHeaders(flask.jsonify({'running': 'True'}))


@app.route('/drive')
def drive_list():

    # Check if it's logged in, if not, do it.
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    if 'status' in flask.session and flask.session['status'].running == True:
        return addHeaders(flask.jsonify({'running': 'True'}))

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

    drive = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

    files_ret = drive.files().list(q="'root' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'").execute()
    file_list = files_ret['files']

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    return addHeaders(flask.jsonify({'running': 'False',
                                     'list': file_list}))


@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return addHeaders(flask.jsonify(authorization_url))


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(drive_redirect)


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return 'Credentials successfully revoked.' + print_index_table()
    else:
        return 'An error occurred.' + print_index_table()


@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>' +
            print_index_table())


def credentials_to_dict(credentials):
    return {'token':            credentials.token,
            'refresh_token':    credentials.refresh_token,
            'token_uri':        credentials.token_uri,
            'client_id':        credentials.client_id,
            'client_secret':    credentials.client_secret,
            'scopes':           credentials.scopes}


def credentials_to_drive(credentials_dict):
    return {'access_token':     credentials_dict['token'],
            'refresh_token':    credentials_dict['refresh_token'],
            'token_uri':        credentials_dict['token_uri'],
            'client_id':        credentials_dict['client_id'],
            'client_secret':    credentials_dict['client_secret'],
            'token_expiry':     None,
            'user_agent':       'Python client library'}


def print_index_table():
    return ('<table>' +
            '<tr><td><a href="/test">Test an API request</a></td>' +
            '<td>Submit an API request and see a formatted JSON response. ' +
            '    Go through the authorization flow if there are no stored ' +
            '    credentials for the user.</td></tr>' +
            '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
            '<td>Go directly to the authorization flow. If there are stored ' +
            '    credentials, you still might not be prompted to reauthorize ' +
            '    the application.</td></tr>' +
            '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
            '<td>Revoke the access token associated with the current user ' +
            '    session. After revoking credentials, if you go to the test ' +
            '    page, you should see an <code>invalid_grant</code> error.' +
            '</td></tr>' +
            '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
            '<td>Clear the access token currently stored in the user session. ' +
            '    After clearing the token, if you <a href="/test">test the ' +
            '    API request</a> again, you should go back to the auth flow.' +
            '</td></tr></table>')


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
