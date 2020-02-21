import flask
import requests
import uuid
from flask_cors import CORS, cross_origin

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from drive_process import ProcessThread, my_status, check_status, clean_status


drive_redirect = 'https://refotos.appspot.com/drive'

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "./client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/drive']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

app = flask.Flask(__name__)
app.secret_key = b'5oZW66$#^#3w3FE3'

# CORS - cross domain config
cors = CORS(app, supports_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'


# ainda não usei! \/
def has_status():
    if 'sid' in flask.session:  # Se tem ID salvo na session
        if check_status(flask.session['sid']):  # Se tem um status salvo para esse ID
            if my_status(flask.session['sid'])['running']:  # Se esse status está em 'running'
                return True
            else:
                clean_status(flask.session['sid'])
                flask.session.pop('sid')
                return False
        else:
            flask.session.pop('sid')
            return False
    else:
        return False


@app.route('/test')
def test_server():
    return '<h1>Servidor Funcionando!</h1>'


# pré rpocessamento de imgs -----------------------------------------------------------------------


@app.route('/list_drive_files')
def drive_list():
    # Check if it's logged in, if not, do it.
    if 'credentials' not in flask.session:
        return flask.redirect('do_authorize')

    # Testes para ver se o processamento já está acontecendo em paralelo (nesse caso redireciona para ele)
    if 'sid' in flask.session:
        if check_status(flask.session['sid']):
            return flask.jsonify({'running': 'True'})
        else:
            flask.session.pop('sid')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    files_ret = drive.files().list(
        q="'root' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'").execute()
    file_list = files_ret['files']

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.jsonify({'running': 'False',
                          'list': file_list})


@app.route('/process_folder/<folder_id>')
def process_folder(folder_id):
    # Check if it's logged in, if not, do it.
    if 'credentials' not in flask.session:
        return flask.redirect('do_authorize')

    # Testes para ver se o processamento já está acontecendo em paralelo (nesse caso redireciona para ele)
    if 'sid' in flask.session:
        if not check_status(flask.session['sid']):
            flask.session.pop('sid')
        else:
            status = my_status(flask.session['sid'])
            if status['running'] is True:
                return flask.jsonify({'running': 'True'})
            elif not status['running']:
                clean_status(flask.session['sid'])
                flask.session.pop('sid')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

    # Generate an ID for the session and status relative to it
    flask.session['sid'] = uuid.uuid4()
    # Create and start the thread that process all the selected folder
    thread = ProcessThread(credentials, folder_id, flask.session['sid'])
    thread.start()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.jsonify({'running': 'True'})


# Enquanto processa imgs --------------------------------------------------------------------------


@app.route('/get_filelist')
def get_fileslist():
    # Testes para ver se o processamento está realmente acontecendo (se não, sinaliza no retorno)
    if 'sid' not in flask.session:
        return flask.jsonify({'running': 'False'})
    if not check_status(flask.session['sid']):
        flask.session.pop('sid')
        return flask.jsonify({'running': 'False'})

    status = my_status(flask.session['sid'])

    if not status['running']:
        clean_status(flask.session['sid'])
        flask.session.pop('sid')
        return flask.jsonify({'running': 'False'})

    return flask.jsonify({'running': 'True',
                          'folder_name': status['folder_name'],
                          'files_list': status['files_list']})


@app.route('/get_status')
def get_status():
    # Testes para ver se o processamento está realmente acontecendo (se não, sinaliza no retorno)
    if 'sid' not in flask.session:
        return flask.jsonify({'running': 'False'})
    if not check_status(flask.session['sid']):
        flask.session.pop('sid')
        return flask.jsonify({'running': 'False'})

    status = my_status(flask.session['sid'])

    if not status['running']:
        clean_status(flask.session['sid'])
        flask.session.pop('sid')
        return flask.jsonify({'running': 'False'})

    return flask.jsonify({'running': 'True',
                          'current_file': status['current_file'],
                          'progress': status['progress']})


@app.route('/cancel_processing')
def cancel_processing():
    # Testes para ver se o processamento está realmente acontecendo (se não, sinaliza no retorno)
    if 'sid' not in flask.session:
        return flask.jsonify({'running': 'False',
                              'done': 'False'})
    if not check_status(flask.session['sid']):
        flask.session.pop('sid')
        return flask.jsonify({'running': 'False',
                              'done': 'False'})

    status = my_status(flask.session['sid'])
    status['cancel_signal'] = True

    status['my_thread'].join()
    if check_status(flask.session['sid']):
        clean_status(flask.session['sid'])
    flask.session.pop('sid')

    return flask.jsonify({'running': 'False',
                          'done': 'True'})


@app.route('/_clean_all')
def clean_all():
    clean_status(flask.session['sid'])
    flask.session.pop('sid')
    return flask.jsonify({'clean': 'yeah it is!'})


# OAuth2 FUNCS ====================================================================================


@app.route('/do_authorize')
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

    return authorization_url


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


@app.route('/revoke_credentials')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke_ret = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke_ret, 'status_code')
    if status_code == 200:
        return 'Credentials successfully revoked.'
    else:
        return 'An error occurred.'


@app.route('/clear_credentials')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return 'Credentials have been cleared.<br><br>'


def credentials_to_dict(credentials):
    return {'token':            credentials.token,
            'refresh_token':    credentials.refresh_token,
            'token_uri':        credentials.token_uri,
            'client_id':        credentials.client_id,
            'client_secret':    credentials.client_secret,
            'scopes':           credentials.scopes}


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run(host='127.0.0.1', port=8080, debug=True)
