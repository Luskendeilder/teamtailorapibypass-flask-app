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
    level=logging.DEBUG,  # Set to DEBUG for detailed logs
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
    'X-Api-Version': '20240404'  # Use the appropriate API version
}

@app.before_request
def log_request_info():
    logger.info(f"Received {request.method} request for {request.path} from {request.remote_addr}")
    logger.debug(f"Query Parameters: {request.args}")

@app.route('/candidate/', defaults={'phone_number': None})
@app.route('/candidate/<path:phone_number>', methods=['GET'])
def get_candidate_info_and_url(phone_number):
    # If phone_number is None or empty, try to get it from the query string
    if not phone_number:
        # Attempt to extract the phone number from the query string
        # This handles URLs like '/candidate/?96005939'
        # The query string will be '96005939' without a key
        query_string = request.query_string.decode('utf-8')
        logger.debug(f"Query string: {query_string}")
        if query_string:
            phone_number = query_string
        else:
            return jsonify({'error': 'Phone number is required.'}), 400

    # Remove leading '?' if present
    if phone_number.startswith('?'):
        phone_number = phone_number[1:]

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
    logger.debug(f"Normalized input phone number: {normalized_input_number}")

    target_phone_number = normalized_input_number
    candidate_found = False

    # Prepare the base64-encoded query and Teamtailor URL
    query_object = {"query": phone_number, "root":[]}
    query_json = json.dumps(query_object, separators=(',', ':'))
    base64_query = base64.b64encode(query_json.encode('utf-8')).decode('utf-8')
    teamtailor_url = f"https://app.teamtailor.com/companies/{COMPANY_ID}/candidates/segment/all?q={base64_query}"

    # Initialize candidate information
    candidate_info = None
    candidate_id = None
    applied_jobs = []

    # Log the beginning of the candidate search
    logger.info(f"Starting search for candidate with phone number: {target_phone_number}")

    # First, get the total number of pages
    page_size = 30  # Maximum allowed page size
    params = {
        'page[size]': page_size,
        'page[number]': 1,  # Start with the first page to get meta information
        'sort': '-id'       # Sort candidates by most recent
    }
    try:
        response = requests.get('https://api.teamtailor.com/v1/candidates', headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Error fetching data from Teamtailor: {response.status_code} - {response.text}")
            return jsonify({'error': 'Error fetching data from Teamtailor.'}), response.status_code
    except Exception as e:
        logger.error(f"Exception occurred while making API request: {e}")
        return jsonify({'error': 'Internal server error'}), 500

    data = response.json()
    total_pages = data.get('meta', {}).get('page-count', 1)
    logger.debug(f"Total pages: {total_pages}")

    # Start from the last page and move backwards
    page_number = 1

    while page_number <= total_pages:
        params['page[number]'] = page_number
        logger.debug(f"Fetching page {page_number}")

        try:
            response = requests.get('https://api.teamtailor.com/v1/candidates', headers=headers, params=params)
            if response.status_code != 200:
                logger.error(f"Error fetching data from Teamtailor: {response.status_code} - {response.text}")
                return jsonify({'error': 'Error fetching data from Teamtailor.'}), response.status_code
        except Exception as e:
            logger.error(f"Exception occurred while making API request: {e}")
            return jsonify({'error': 'Internal server error'}), 500

        data = response.json()
        candidates = data.get('data', [])

        if not candidates:
            logger.info("No more candidates to process.")
            break

        # Iterate through the candidates
        for candidate in candidates:
            candidate_phone = candidate['attributes'].get('phone')
            candidate_id = candidate['id']
            logger.debug(f"Processing candidate ID: {candidate_id}, Phone: {candidate_phone}")

            if candidate_phone:
                # Normalize the stored phone number
                try:
                    stored_number = phonenumbers.parse(candidate_phone, None)
                except phonenumbers.NumberParseException:
                    # Try parsing with default country code
                    try:
                        stored_number = phonenumbers.parse(candidate_phone, 'NO')
                    except phonenumbers.NumberParseException:
                        # Skip if the stored phone number is invalid
                        logger.warning(f"Invalid stored phone number format for candidate ID {candidate_id}: {candidate_phone}")
                        continue

                normalized_stored_number = phonenumbers.format_number(
                    stored_number, phonenumbers.PhoneNumberFormat.E164
                )
                logger.debug(f"Candidate ID {candidate_id}: Normalized stored phone number: {normalized_stored_number}")

                # Compare the normalized phone numbers
                if normalized_stored_number == target_phone_number:
                    # Candidate found
                    first_name = candidate['attributes'].get('first-name', '')
                    last_name = candidate['attributes'].get('last-name', '')
                    email = candidate['attributes'].get('email', '')
                    candidate_id = candidate['id']
                    candidate_info = {
                        'candidate_id': candidate_id,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email
                    }
                    candidate_found = True
                    logger.info(f"Candidate found: {first_name} {last_name}, ID: {candidate_id}")
                    break
            else:
                logger.debug(f"No phone number for candidate ID {candidate_id}")

        # Break if candidate is found
        if candidate_found:
            break

        # Move to the next page
        page_number += 1

    # If candidate is found, fetch their job applications
    if candidate_found and candidate_id:
        applications_url = f"https://api.teamtailor.com/v1/candidates/{candidate_id}/job-applications"
        params = {
            'include': 'job'
        }
        try:
            response_applications = requests.get(applications_url, headers=headers, params=params)
            if response_applications.status_code == 200:
                applications_data = response_applications.json()
                job_applications = applications_data.get('data', [])
                included = applications_data.get('included', [])

                # Create a mapping of job IDs to job data
                jobs_dict = {item['id']: item for item in included if item['type'] == 'jobs'}

                # Iterate over applications to get job details
                for application in job_applications:
                    job_data = application['relationships'].get('job', {}).get('data')
                    if job_data:
                        job_id = job_data.get('id')
                        job = jobs_dict.get(job_id)
                        if job:
                            job_internal_name = job['attributes'].get('internal-name')
                            applied_jobs.append({
                                'job_id': job_id,
                                'internal_name': job_internal_name
                            })
            else:
                logger.error(f"Error fetching job applications: {response_applications.status_code} - {response_applications.text}")
        except Exception as e:
            logger.error(f"Exception occurred while fetching job applications: {e}")
    else:
        applied_jobs = None

    # Prepare the response with ttquery nested
    response_data = {
        'candidate_info': candidate_info,
        'applied_jobs': applied_jobs,
        'ttquery': {
            'base64_query': base64_query,
            'teamtailor_url': teamtailor_url
        }
    }

    if candidate_info:
        logger.info("Returning candidate information.")
        return jsonify(response_data)
    else:
        logger.info("No candidate found with that phone number.")
        return jsonify({
            'error': 'No candidate found with that phone number.',
            'ttquery': {
                'base64_query': base64_query,
                'teamtailor_url': teamtailor_url
            }
        }), 404

@app.after_request
def log_response_info(response):
    logger.info(f"Response status: {response.status}")
    return response

if __name__ == '__main__':
    app.run()
