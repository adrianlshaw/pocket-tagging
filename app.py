#!/usr/bin/env python3
import requests
import json
import http.client
import webbrowser
from urllib.parse import parse_qs, urlparse, urlencode
import os, sys
import spacy
import datetime

redirect_uri = 'http://localhost'
# Pocket API endpoint for retrieving bookmarks
endpoint = 'https://getpocket.com/v3/get'
headers = {
    "Content-Type": "application/json",
    "X-Accept": "application/json"
}

ACCESS_TOKEN_FILE = 'access_token.txt'

def delete_all_tags(consumer_key, access_token):
    # Pocket API endpoint for retrieving bookmarks
    get_endpoint = 'https://getpocket.com/v3/get'

    # Pocket API endpoint for modifying bookmarks
    send_endpoint = 'https://getpocket.com/v3/send'

    # Prepare the request payload to get bookmarks
    get_payload = {
        'consumer_key': consumer_key,
        'access_token': access_token,
        'state': 'all',
        'detailType': 'complete'
    }

    # Send a POST request to the Pocket API to get bookmarks
    get_response = requests.post(get_endpoint, headers=headers, data=json.dumps(get_payload))

    # Check if the request was successful
    if get_response.status_code == 200:
        get_data = get_response.json()

        # Extract bookmark details from the response
        bookmarks = get_data.get('list', {})

        # Prepare the request payload to remove tags
        send_payload = {
            'consumer_key': consumer_key,
            'access_token': access_token,
            'actions': []
        }

        # Iterate through bookmarks and add actions to remove tags
        for item_id in bookmarks.keys():
            send_payload['actions'].append({
                'action': 'tags_clear',
                'item_id': item_id
            })

        # Send a POST request to the Pocket API to remove tags
        send_response = requests.post(send_endpoint, headers=headers, data=json.dumps(send_payload))

        # Check if the request was successful
        if send_response.status_code == 200:
            send_data = send_response.json()

            # Check the response for any errors
            if send_data.get('status') == 1:
                print('All tags deleted successfully.')
            else:
                print('Error:', send_data.get('error'))
        else:
            print('Error:', send_response.status_code)
    else:
        print('Error:', get_response.status_code)

def add_tags_to_bookmark(consumer_key, access_token, bookmark_item_id, tags):
    # Pocket API endpoint for modifying bookmarks
    endpoint = 'https://getpocket.com/v3/send'

    # Prepare the request payload
    payload = {
        'consumer_key': consumer_key,
        'access_token': access_token,
        'actions': [
            {
                'action': 'tags_add',
                'item_id': bookmark_item_id,
                'tags': tags
            }
        ]
    }

    # Send a POST request to the Pocket API
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        # Check the response for any errors
        if data.get('status') == 1:
            print('Tags assigned successfully.')
        else:
            print('Error:', data.get('error'))
    else:
        print('Error:', response.status_code)

    # Send a POST request to the Pocket API
    response = requests.post(endpoint, data=json.dumps(payload))

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

def get_access_token_from_file():
    if os.path.exists(ACCESS_TOKEN_FILE):
        # Access token file exists, read the access token from it
        with open(ACCESS_TOKEN_FILE, 'r') as file:
            access_token = file.read().strip()
            return access_token


def get_access_token(consumer_key):
    # Step 1: Obtain a request token
    request_token_endpoint = 'https://getpocket.com/v3/oauth/request'
    request_payload = {
        'consumer_key': consumer_key,
        'redirect_uri': redirect_uri  # Replace with your desired redirect URI
    }
    response = requests.post(request_token_endpoint, data=request_payload)
    if response.status_code == 200:
        request_token = parse_qs(response.text)['code'][0]
        print(request_token)
    else:
        raise Exception('Error obtaining request token:', response.status_code)

    # Step 2: Authorize the application
    authorize_url = f'https://getpocket.com/auth/authorize?request_token={request_token}&redirect_uri={redirect_uri}'
    print('Please visit the following URL to authorize the application:')
    webbrowser.open(authorize_url, new=2)
    print(authorize_url)
    input('Press Enter to continue after authorization...')

    # Step 3: Obtain the access token
    access_token_endpoint = 'https://getpocket.com/v3/oauth/authorize'
    access_token_payload = {
        'consumer_key': consumer_key,
        'code': request_token
    }
    response = requests.post(access_token_endpoint, data=access_token_payload)
    if response.status_code == 200:
        at = response.text.split('=')[1]
        access_token = at.split('&')[0]
        return access_token
    else:
        error_message = http.client.responses.get(response.status_code)
        raise Exception('Error obtaining access token:', response.status_code, error_message)


# Replace with your Pocket API consumer key
consumer_key = 'f00f00-f00f00babaf00f00f00bad'

access_token = get_access_token_from_file()
if access_token == None:
    access_token = get_access_token(consumer_key)
    with open(ACCESS_TOKEN_FILE, 'w') as file:
            file.write(access_token)
            file.close()

print("Consumer key: " + consumer_key)
print("Access   key: " + access_token)

payload = {
    'consumer_key': consumer_key,
    'access_token': access_token,
    'state': 'all',
    'sort': 'newest',
    'detailType': 'complete'
}

api_url = f'{endpoint}?{urlencode(payload)}'
print('Full Request URL:', api_url)

#delete_all_tags(consumer_key, access_token)

# Send a POST request to the Pocket API
response = requests.post(endpoint, headers=headers, data=json.dumps(payload))

nlp = spacy.load('en_core_web_sm')

# Check if the request was successful
if response.status_code == 200:
    data = response.json()

    # Extract bookmark titles from the response
    bookmarks = data.get('list', {})
    for bookmark in bookmarks.values():
        title = bookmark.get('resolved_title')
        url = bookmark.get('given_url')
        content = bookmark.get('excerpt', '')
        item_id = bookmark.get('item_id')

        if url:
            bookmark_doc = nlp(content)
            keywords = [token.lemma_ for token in bookmark_doc if not token.is_stop and token.pos_ in ['NOUN', 'VERB']]
            tags = keywords[:3]  # Limit to three tags per URL
            if title:

                #add_tags_to_bookmark(consumer_key, access_token, item_id, tags)
                timestamp = bookmark.get('time_added')

                # Convert the timestamp to a human-readable date
                date = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
                print(date + " " + title + " " + url)
                print(tags)



else:
    print('Error:', response.status_code)
