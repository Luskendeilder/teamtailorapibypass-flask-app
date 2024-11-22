from flask import Flask, jsonify, request
import os
import json
import base64
import requests
import logging
import phonenumbers

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
logger = logging.getLogger(__name__)

# Get environment variables
API_KEY = os.environ.get('API_KEY')          # Your Teamtailor API key
COMPANY_ID = os.environ.get('COMPANY_ID')    # Your Teamtailor company ID

# Set up headers for the Teamtailor API
headers = {
    'Authorization': f'Token token={API_KEY}',
    'Content-Type': 'application/vnd.api+json',
    'X-Api-Version': '20240904'
}

@app.before_request
def log_request_info():
    logger.info(f"Received {request.method} request for {request.path} from {request.remote_addr}")
    # Optionally, log query parameters if they don't contain sensitive information
    logger.debug(f"Query Parameters: {request.args}")

@app.route('/candidate/<phone_number>', methods=['GET'])
def get_candidate_info_and_url(phone_number):
    # Normalize the input phone number
    try:
        # Attempt to parse with no region first
        input_number = phonenumbers.parse(phone_number, None)
    except phonenumbers.NumberParseException:
        # If parsing fails, assume default country (e.g., 'NO' for Norway)
        try:
            input_number = phonenumbers.parse(phone_number, 'NO')
        except phonenumbers.NumberParseException:
            logger.error(f"Invalid phone number format: {phone_number}")
            return jsonify({'error': 'Invalid phone number format.'}), 400

    normalized_input_number = phonenumbers.format_number(
        input_number, phonenumbers.PhoneNumberFormat.E164
    )

    target_phone_number = normalized_input_number
    next_cursor = None
    candidate_found = False

    # Prepare the base64-encoded query and Teamtailor URL
    query_object = {"query": phone_number, "root":[]}
    query_json = json.dumps(query_object, separators=(',', ':'))
    base64_query = base64.b64encode(query_json.encode('utf-8')).decode('utf-8')
    teamtailor_url = f"https://app.teamtailor.com/companies/{COMPANY_ID}/candidates/segment/all?q={base64_query}"

    # Initialize candidate information
    candidate_info = None

    # Log the beginning of the candidate search
    logger.info(f"Starting search for candidate with phone number: {target_phone_number}")

    # Search for the candidate using the Teamtailor API
    while True:
        params = {}
        if next_cursor:
            params['page[after]'] = next_cursor

        try:
            response = requests.get('https://api.teamtailor.com/v1/candidates', headers=headers, params=params)
        except Exception as e:
            logger.error(f"Exception occurred while making API request: {e}")
            return jsonify({'error': 'Internal server error'}), 500

        if response.status_code == 200:
            data = response.json()
            candidates = data.get('data', [])

            # Iterate through the candidates
            for candidate in candidates:
                phone = candidate['attributes'].get('phone')
                if phone:
                    # Normalize the stored phone number
                    try:
                        stored_number = phonenumbers.parse(phone, None)
                    except phonenumbers.NumberParseException:
                        # Try parsing with default country code
                        try:
                            stored_number = phonenumbers.parse(phone, 'NO')
                        except phonenumbers.NumberParseException:
                            # Skip if the stored phone number is invalid
                            logger.warning(f"Invalid stored phone number format: {phone}")
                            continue

                    normalized_stored_number = phonenumbers.format_number(
                        stored_number, phonenumbers.PhoneNumberFormat.E164
                    )

                    # Compare the normalized phone numbers
                    if normalized_stored_number == target_phone_number:
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
                        logger.info(f"Candidate found: {first_name} {last_name}")
                        break

            # Break if candidate is found
            if candidate_found:
                break

            # Check for pagination
            next_cursor = data.get('meta', {}).get('cursors', {}).get('after')
            if not next_cursor:
                logger.info("Reached end of candidate list without finding a match.")
                break
        else:
            logger.error(f"Error fetching data from Teamtailor: {response.status_code} - {response.text}")
            return jsonify({'error': 'Error fetching data from Teamtailor.'}), response.status_code

    # Prepare the response
    response_data = {
        'candidate_info': candidate_info,
        'base64_query': base64_query,
        'teamtailor_url': teamtailor_url
    }

    if candidate_info:
        logger.info("Returning candidate information.")
        return jsonify(response_data)
    else:
        logger.info("No candidate found with that phone number.")
        return jsonify({
            'error': 'No candidate found with that phone number.',
            'base64_query': base64_query,
            'teamtailor_url': teamtailor_url
        }), 404

@app.after_request
def log_response_info(response):
    logger.info(f"Response status: {response.status}")
    return response

if __name__ == '__main__':
    app.run()
