from flask import Flask, jsonify
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
def get_candidate_info_and_url(phone_number):
    target_phone_number = phone_number
    next_cursor = None
    candidate_found = False

    # Prepare the base64-encoded query and Teamtailor URL
    query_object = {"query": phone_number, "root":[]}
    query_json = json.dumps(query_object, separators=(',', ':'))
    base64_query = base64.b64encode(query_json.encode('utf-8')).decode('utf-8')
    teamtailor_url = f"https://app.teamtailor.com/companies/{COMPANY_ID}/candidates/segment/all?q={base64_query}"

    # Initialize candidate information
    candidate_info = None

    # Search for the candidate using the Teamtailor API
    while True:
        params = {}
        if next_cursor:
            params['page[after]'] = next_cursor

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
                    candidate_info = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email
                    }
                    candidate_found = True
                    break

            # Break if candidate is found
            if candidate_found:
                break

            # Check for pagination
            next_cursor = data.get('meta', {}).get('cursors', {}).get('after')
            if not next_cursor:
                break
        else:
            return jsonify({'error': 'Error fetching data from Teamtailor.'}), response.status_code

    # Prepare the response
    response_data = {
        'candidate_info': candidate_info,
        'base64_query': base64_query,
        'teamtailor_url': teamtailor_url
    }

    if candidate_info:
        return jsonify(response_data)
    else:
        return jsonify({
            'error': 'No candidate found with that phone number.',
            'base64_query': base64_query,
            'teamtailor_url': teamtailor_url
        }), 404

if __name__ == '__main__':
    app.run()
