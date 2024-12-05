from flask import Flask, render_template, request, redirect, url_for
import requests
import json
from datetime import datetime
import pymysql
from utils import save_appointment  # Import save_appointment from utils
from db_utils import get_db_connection  # Import get_db_connection from db_utils


app = Flask(__name__)

API_URL = "https://data.cms.gov/provider-data/api/1/datastore/query/0127-af37/0"  # Pulmonary Disease Office Visit Costs

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    # Get form data
    location = request.form.get('location')
    radius = request.form.get('radius')

    # Prepare the data for the API request
    data = {
        "conditions": [
            {
                "resource": "t",
                "property": "zip_code",  # Filter based on zip code
                "value": location,
                "operator": "="  # Exact match
            }
        ],
        "limit": 10  # Adjust the limit to your needs
    }

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        try:
            results = response.json()
            records = results.get('results', [])

            if not records:
                result = {"message": f"No data found for zip code {location}."}
            else:
                result = {"location": location, "radius": radius, "records": records}

            # Pass the location to the results page
            return render_template('results.html', result=result)

        except json.JSONDecodeError:
            return f"Error: Response is not in valid JSON format. Raw Response: {response.text}"
    else:
        return f"Error: {response.status_code}"

@app.route('/check_appointments', methods=['GET', 'POST'])
def check_appointments():
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        patient_phone = request.form['patient_phone']

        # Search the appointments table for matching records
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Updated column name 'patient_phone_number' in the query
        query = """
        SELECT * FROM appointments
        WHERE patient_full_name = %s AND patient_phone_number = %s
        """
        cursor.execute(query, (patient_name, patient_phone))
        appointments = cursor.fetchall()
        connection.close()

        # If no appointments are found, inform the user
        if not appointments:
            return render_template('check_appointments.html', message="No appointments found for the given details.")

        return render_template('check_appointments.html', appointments=appointments)

    return render_template('check_appointments.html')



url = "https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0"

@app.route('/physician')
def physician():
    # Get ZIP code from query parameters
    location = request.args.get('location')  # Retrieve location passed as a query parameter
    search_zip_code = location[:5]  # Use only the first 5 digits of the ZIP code

    response = requests.get(url)

    physicians = []
    if response.status_code == 200:
        data = response.json()

        for record in data.get('results', []):
            provider_zip_code = str(record.get('zip_code', ''))[:5]

            if provider_zip_code == search_zip_code:
                physicians.append({
                    'last_name': record.get('provider_last_name', 'N/A'),
                    'first_name': record.get('provider_first_name', 'N/A'),
                    'specialty': record.get('pri_spec', 'N/A'),
                    'zip_code': provider_zip_code,
                    'telephone_number': record.get('telephone_number', 'N/A'),
                    'facility_name': record.get('facility_name', 'N/A')
                })
    else:
        print("Failed to retrieve data:", response.status_code)

    return render_template('physician.html', physicians=physicians, location=location)

@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if request.method == 'GET':
        physician_name = request.args.get('physician_name')
        location = request.args.get('location')
        specialty = request.args.get('specialty')  # Capture specialty
        facility_name = request.args.get('facility_name')  # Capture facility_name

        # Render template with the added fields
        return render_template('book_appointment.html', physician_name=physician_name, location=location, specialty=specialty, facility_name=facility_name)

    elif request.method == 'POST':
        patient_full_name = request.form['patient_full_name']
        appointment_date = request.form['appointment_date']
        physician_name = request.form['physician_name']
        location = request.form['location']
        patient_telephone_number = request.form['patient_telephone_number']
        patient_email = request.form['patient_email']
        
        # Fetch specialty and facility_name (these values are now passed through the form in the GET request)
        specialty = request.form['specialty']  # Get from the form, as it's now part of the form
        facility_name = request.form['facility_name']  # Get from the form

        # Save the appointment, passing all necessary fields including appointment_date
        save_appointment(patient_full_name, appointment_date, physician_name, specialty, facility_name, patient_telephone_number, patient_email, location, patient_telephone_number)

        return redirect(url_for('appointment_successful'))


@app.route('/appointments')
def appointments():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM appointments ORDER BY created_at DESC LIMIT 1")
    # cursor.execute("SELECT * FROM appointments")
    # cursor.execute("SELECT * FROM appointments ORDER BY created_at DESC LIMIT 1")
    appointments = cursor.fetchall()
    connection.close()
    return render_template('appointments.html', appointments=appointments)

@app.route('/appointment_successful')
def appointment_successful():
    return render_template('appointment_successful.html')


# New route for analyzing and comparing two locations
@app.route('/analyze', methods=['GET'])
def analyze():
    # Get the two location values from the query parameters
    location1 = request.args.get('location1')
    location2 = request.args.get('location2')

    # Prepare the data for the API request (for location 1)
    data = {
        "conditions": [
            {
                "resource": "t",
                "property": "zip_code",  # Filter based on zip code
                "value": location1,
                "operator": "="  # Exact match
            }
        ],
        "limit": 10  # Adjust the limit to your needs
    }

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Fetch data for the first location
    response1 = requests.post(API_URL, headers=headers, data=json.dumps(data))

    # Modify the data for the second location
    data["conditions"][0]["value"] = location2  # Modify the data to query the second location

    # Fetch data for the second location
    response2 = requests.post(API_URL, headers=headers, data=json.dumps(data))

    if response1.status_code == 200 and response2.status_code == 200:
        try:
            results1 = response1.json()
            results2 = response2.json()

            records1 = results1.get('results', [])
            records2 = results2.get('results', [])

            # Prepare result for both locations
            result = {
                "location1": location1, "location2": location2,
                "records1": records1, "records2": records2
            }

            # Pass the result to the analysis template
            return render_template('analysis.html', result=result)

        except json.JSONDecodeError:
            return f"Error: Response is not in valid JSON format. Raw Response: {response1.text} and {response2.text}"
    else:
        return f"Error: {response1.status_code} and {response2.status_code}"
    
if __name__ == '__main__':
    app.run(debug=True)
