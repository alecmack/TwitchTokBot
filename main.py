import os
import requests
import socket
import time
import webbrowser
from downloadLink import extract_clip_video_url
from flask import Flask, request, redirect
from threading import Thread

# Twitch API credentials
CLIENT_ID = os.environ['TWITCH_CLIENT_ID']
CLIENT_SECRET = os.environ['TWITCH_CLIENT_SECRET']

REDIRECT_URI = 'http://localhost:3000/callback'
SCOPE = 'clips:edit'  # Scope required for clipping streams

APP_ROUTE = 'http://localhost:3000'

authorization_code = None
access_token = None
stream_id = None

# Channel to monitor
CHANNEL_NAME = 'clix'

# Clip parameters
DURATION = '30'  # Duration of the clip in seconds

# Clip endpoint
clip_endpoint = 'https://api.twitch.tv/helix/clips'

# Twitch API endpoints
TWITCH_API_BASE_URL = 'https://api.twitch.tv/helix/'
AUTH_URL = 'https://id.twitch.tv/oauth2/token'

# Twitch IRC server details
TWITCH_IRC_SERVER = 'irc.chat.twitch.tv'
TWITCH_IRC_PORT = 6667

# Define your Twitch bot's credentials
BOT_USERNAME = 'xan'
OAUTH_TOKEN = 'oauth:9zpl34wccjbp6a006whbbb33awcy8k'


# Flask server to automate authorization code access
app = Flask(__name__)


@app.route('/')
def home():
    return redirect(f'https://id.twitch.tv/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPE}')


@app.route('/callback')
def callback():
    global authorization_code, access_token, stream_id
    authorization_code = request.args.get('code')

    access_token = get_access_token()

    stream_id = get_stream_id()

    # print("access token: " + access_token)
    # print(authorization_code)

    return "auth code: " + authorization_code


def run_flask_app():
    app.run(debug=False, port=3000)


def monitor_chat():

    print("begin monitoring " + CHANNEL_NAME + "'s chat")
    # Connect to Twitch IRC server
    irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc_socket.connect((TWITCH_IRC_SERVER, TWITCH_IRC_PORT))

    # Authenticate with Twitch IRC server
    irc_socket.send(f"PASS {OAUTH_TOKEN}\n".encode('utf-8'))
    irc_socket.send(f"NICK {BOT_USERNAME}\n".encode('utf-8'))
    irc_socket.send(f"JOIN #{CHANNEL_NAME}\n".encode('utf-8'))

    message_count = 0
    prev_count = 0
    start_time = time.time()

    print("messages: ")
    # Listen for messages
    while True:
        # Receive data from Twitch IRC server
        response = irc_socket.recv(2048).decode('utf-8')

        elapsed_time = time.time() - start_time

        if elapsed_time >= 10:
            print(str(message_count) + "...", end="")

            if 0 < prev_count * 3 < message_count:
                print("Spike detected! Clipping stream...")
                clip_stream()

            prev_count = message_count
            message_count = 0
            start_time = time.time()

        # Print received data (you may want to parse and filter the messages)
        if 'PRIVMSG' in response:
            message_count += 1

        if response.startswith("PING"):
            ping_msg = response.split()[1]
            irc_socket.send(f"PONG {ping_msg}\n".encode("utf-8"))

        # Add a sleep to prevent excess load on the IRC server
        time.sleep(0.01)


# Function to authenticate with Twitch API and get access token
def get_access_token():
    params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': authorization_code,
        'scope': SCOPE,
    }

    response = requests.post(AUTH_URL, data=params)
    data = response.json()

    token = data['access_token']

    return token


# Function to fetch chat activity
def get_stream_id():
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(f'{TWITCH_API_BASE_URL}streams?user_login={CHANNEL_NAME}', headers=headers)
    data = response.json()

    # print(data)

    try:
        stream_id = data['data'][0]['user_id']

    except IndexError:
        raise Exception(CHANNEL_NAME + " appears to be offline, check the stream for activity, or try again later")


    #print(stream_id)

    print("stream_id: " + stream_id)

    return stream_id


def clip_stream():

    # Request headers
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Clip creation request payload
    clip_data = {
        'broadcaster_id': stream_id,
        'duration': DURATION
    }

    response = requests.post(clip_endpoint, headers=headers, json=clip_data)

    if response.status_code == 202:
        # Clip created successfully
        clip_response = response.json()
        clip_url = clip_response['data'][0]['edit_url']

        clip_url = clip_url.rsplit('/',1)[0]

        print(clip_url)

        extract_clip_video_url(clip_url, CHANNEL_NAME)

    else:
        print("error generating clip")


if __name__ == "__main__":

    # creates separate thread for server application
    thread = Thread(target=run_flask_app)
    thread.start()

    # Allows time for server to start
    time.sleep(2)

    webbrowser.open(APP_ROUTE)

    monitor_chat()

