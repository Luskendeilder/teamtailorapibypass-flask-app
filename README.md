Teamtailor Candidate API Bypass
This Flask application provides an API endpoint to retrieve candidate information from the Teamtailor API based on a phone number. It bypasses the limitation of the Teamtailor API, which does not support direct filtering by phone number, by iterating through candidates and matching the phone numbers.

Features
Retrieves candidate information based on a provided phone number.
Returns candidate details including first name, last name, email, and creation date.
Displays the creation date in dd-mm-yyyy format.
Provides a list of jobs the candidate has applied for.
Generates a Teamtailor URL with a base64-encoded query to directly access the candidate in the Teamtailor web app.
Handles phone numbers provided in various formats, including URL-encoded '+' signs (%2B).
Hosted on Heroku for easy deployment and scalability.
Demo
An example API call:

perl
Copy code
https://your-app.herokuapp.com/candidate/?%2B4746874777
Table of Contents
Prerequisites
Installation
Configuration
Deployment to Heroku
Usage
API Response Example
Logging and Monitoring
Contributing
License
Prerequisites
Python 3.6 or higher
A Teamtailor API key with the necessary permissions
A Teamtailor company ID
A Heroku account (for deployment)
Git (for version control and deployment)
Installation
Clone the Repository

bash
Copy code
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
Create a Virtual Environment

bash
Copy code
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install Dependencies

bash
Copy code
pip install -r requirements.txt
Contents of requirements.txt:

makefile
Copy code
Flask==2.0.3
requests==2.26.0
phonenumbers==8.12.34
gunicorn==20.1.0
Configuration
Set Environment Variables

Create a .env file in the project root or set the environment variables in your system:

API_KEY: Your Teamtailor API key.
COMPANY_ID: Your Teamtailor company ID.
Example .env file:

bash
Copy code
API_KEY=your_teamtailor_api_key
COMPANY_ID=your_teamtailor_company_id
Important: Never commit your .env file or API keys to version control.

Update the Application (Optional)

If needed, update the app.py file with any custom configurations or additional features.

Deployment to Heroku
Create a Heroku App

bash
Copy code
heroku login
heroku create your-app-name
Set Environment Variables on Heroku

bash
Copy code
heroku config:set API_KEY=your_teamtailor_api_key
heroku config:set COMPANY_ID=your_teamtailor_company_id
Add the Heroku Remote

bash
Copy code
heroku git:remote -a your-app-name
Deploy to Heroku

bash
Copy code
git add .
git commit -m "Initial commit"
git push heroku master
Scale the Web Process

bash
Copy code
heroku ps:scale web=1
Verify Deployment

Visit https://your-app-name.herokuapp.com/ to verify the app is running.

Usage
API Endpoint
URL Format:

arduino
Copy code
https://your-app.herokuapp.com/candidate/?[phone_number]
The phone number can include a '+' sign, which should be URL-encoded as '%2B'.

Example with URL-encoded '+':

perl
Copy code
https://your-app.herokuapp.com/candidate/?%2B4746874777
Parameters
phone_number: The candidate's phone number to search for.
Response
The API returns a JSON response containing:

candidate_info: Candidate details.
applied_jobs: List of jobs the candidate has applied for.
ttquery: Contains a base64-encoded query and a Teamtailor URL to directly access the candidate in the Teamtailor web app.
Example Request
bash
Copy code
curl "https://your-app.herokuapp.com/candidate/?%2B4746874777"
Example Response
json
Copy code
{
  "candidate_info": {
    "candidate_id": "123456",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "created_date": "29-10-2020"
  },
  "applied_jobs": [
    {
      "job_id": "78910",
      "internal_name": "Senior Developer"
    }
  ],
  "ttquery": {
    "base64_query": "eyJxdWVyeSI6Iis0NzQ2ODc0Nzc3Iiwicm9vdCI6W119",
    "teamtailor_url": "https://app.teamtailor.com/companies/your_company_id/candidates/segment/all?q=eyJxdWVyeSI6Iis0NzQ2ODc0Nzc3Iiwicm9vdCI6W119"
  }
}
Error Handling
If the candidate is not found:

json
Copy code
{
  "error": "No candidate found with that phone number.",
  "ttquery": {
    "base64_query": "...",
    "teamtailor_url": "..."
  }
}
If the phone number is invalid or missing:

json
Copy code
{
  "error": "Invalid phone number format."
}
Logging and Monitoring
View Logs

Use the Heroku CLI to view application logs:

bash
Copy code
heroku logs --tail
Logging Levels

The application is configured to use the INFO logging level in production.
Change the logging level to DEBUG in app.py for detailed logs during development.
Files in the Repository
app.py: The main Flask application file.
requirements.txt: Lists the Python dependencies.
Procfile: Specifies the commands that are executed by Heroku to start your app.
runtime.txt: (Optional) Specifies the Python runtime version.
README.md: This file.
Security Considerations
API Keys

Keep your API_KEY and COMPANY_ID secure.
Do not commit them to version control or expose them in logs.
Sensitive Data

Avoid logging sensitive information like full phone numbers or candidate details in production logs.
Contributing
Contributions are welcome! Please follow these steps:

Fork the Repository

Click on the 'Fork' button at the top right corner of this page.

Clone Your Fork

bash
Copy code
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
Create a Feature Branch

bash
Copy code
git checkout -b feature/your-feature-name
Make Changes and Commit

bash
Copy code
git add .
git commit -m "Add your feature"
Push to Your Fork

bash
Copy code
git push origin feature/your-feature-name
Submit a Pull Request

Go to your fork on GitHub and click on 'New pull request'.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgements
Teamtailor API Documentation
Flask Documentation
Heroku Documentation
Contact
For any questions or support, please open an issue on GitHub

