from flask import Flask, redirect, jsonify
import os
import json
import base64
import requests

app = Flask(__name__)

# Get environment variables
API_KEY = os.environ.get('API_KEY')          # Your Teamtailor API key
COMPANY_ID = os.environ.get('COMPANY_ID')    # Your Teamtailor company ID

# Set up headers for the Teamtailor API
headers = {
    'Authorization': f'Token token={API_KEY}',
    'Content-Type': 'application/vnd.api+json',
    'X-Api-Version': '20240904'
}

@app.route('/candidate/<phone_number>', methods=['GET'])
def get_candidate_info(phone_number):
    target_phone_number = phone_number
    next_cursor = None

    while True:
        params = {}
        if next_cursor:
            params['page[after]'] = next_cursor

        # Make the GET request to the candidates endpoint
        response = requests.get('https://api.teamtailor.com/v1/candidates', headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            candidates = data.get('data', [])

            # Iterate through the candidates
            for candidate in candidates:
                phone = candidate['attributes'].get('phone')
                if phone == target_phone_number:
                    # Candidate found
                    first_name = candidate['attributes'].get('first-name', '')
                    last_name = candidate['attributes'].get('last-name', '')
                    email = candidate['attributes'].get('email', '')

                    # Return the candidate's name and email
                    return jsonify({
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email
                    })

            # Check for pagination
            next_cursor = data.get('meta', {}).get('cursors', {}).get('after')
            if not next_cursor:
                break
        else:
            return jsonify({'error': 'Error fetching data from Teamtailor.'}), response.status_code

    return jsonify({'error': 'No candidate found with that phone number.'}), 404

@app.route('/candidateurl/<phone_number>', methods=['GET'])
def get_candidate_url(phone_number):
    # Step 1: Create the JSON object
    query_object = {"query": phone_number, "root":[]}
    # Step 2: Convert to JSON string without spaces
    query_json = json.dumps(query_object, separators=(',', ':'))
    # Step 3: Base64 encode the JSON string
    query_base64 = base64.b64encode(query_json.encode('utf-8')).decode('utf-8')
    # Return the base64-encoded query string
    return jsonify({'base64_query': query_base64})

if __name__ == '__main__':
    app.run()
