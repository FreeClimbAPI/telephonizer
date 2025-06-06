import freeclimb
from flask import Flask, jsonify, request
import os
import requests
from dotenv import load_dotenv
import threading
import time

load_dotenv()
app = Flask(__name__)
global recordings
recordings = {}


def download_file(url_download, url, auth, file_name):
    response = requests.get(url_download, auth=auth)
    # If we are good, create the utterance file name and download it locally.
    if response.status_code == 200:
        print("Dowloading")
        # Create the output directory if it doesn't exist and the variable isn't empty string.
        if not os.path.exists(os.environ['OUTPUT_DIRECTORY']):
            os.makedirs(os.environ['OUTPUT_DIRECTORY'])
        with open(file_name, 'wb') as wavFile:
            wavFile.write(response.content)
    else:
        print("Error: Download failed")


# Specify this route with 'VOICE URL' in App Config
@app.route('/incomingCall', methods=['POST', 'GET'])
def post_incoming_call():
    message = "Start playback"
    say = freeclimb.Say(text=message)
    redirect = freeclimb.Redirect(action_url=os.environ['NGROK_URL'] + "/mainMenu")
    script = freeclimb.PerclScript(commands=[say, redirect])
    return script.to_json()


# Specify this route with 'STATUS CALLBACK URL' in App Config
@app.route('/status', methods=['POST'])
def status():
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/mainMenu', methods=['POST'])
def main_menu():
    print("Main menu")
    resp = request.json
    callId = resp['callId']
    recordings[callId] = time.time()
    record = freeclimb.RecordUtterance(
            action_url= os.environ['NGROK_URL'] + '/collectID',
            auto_start=False,
            play_beep=True,
            silence_timeout_ms=60 * 10000,
            max_length_sec=int(7*3600))
    script = freeclimb.PerclScript(commands=[record])
    return script.to_json()


@app.route('/collectID', methods=['POST'])
def collectID():
    resp = request.json
    print(resp)
    callId = resp['callId']
    phoneNumber = resp['from']
    timestamp = recordings.pop(callId)
    file_name = "{}/rec_{}_{}_{}.wav".format(os.environ['OUTPUT_DIRECTORY'], callId, phoneNumber, timestamp)
    url = os.environ['FC_API_URL'] + "/Accounts/" + os.environ['FC_ACCOUNT_ID'] + "/Recordings/" + resp['recordingId']
    url_download = url + "/Download"
    auth = (os.environ['FC_ACCOUNT_ID'], os.environ['FC_API_KEY'])
    thread = threading.Thread(target = download_file, args=(url_download, url, auth, file_name))
    thread.start()

    hangup = freeclimb.Hangup(reason="Done")
    script = freeclimb.PerclScript(commands=[hangup])
    print(recordings)
    return script.to_json()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)

