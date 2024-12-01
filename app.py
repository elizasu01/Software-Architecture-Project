# Function: check the cost

from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Endpoint to fetch visit cost data
@app.route('/visit-cost', methods=['POST'])
def visit_cost():
    try:
        # Get the zip code and patient type from the request
        data = request.json
        zip_code_input = data.get('zip_code')
        new_patient = data.get('new_patient')

        # URL for the POST request to the CMS API
        url = "https://data.cms.gov/provider-data/api/1/datastore/query/0127-af37/0"

        # Headers and data for the request
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        post_data = {
            "conditions": [
                {
                    "resource": "t",
                    "property": "zip_code",
                    "value": zip_code_input,
                    "operator": "="
                }
            ],
            "limit": 10
        }

        # Send the POST request
        response = requests.post(url, headers=headers, data=json.dumps(post_data))
        if response.status_code == 200:
            results = response.json().get('results', [])

            # Format response based on patient type
            formatted_results = []
            for record in results:
                if new_patient == 'yes':
                    formatted_results.append({
                        "zip_code": record.get('zip_code', 'N/A'),
                        "min_pricing": record.get('min_medicare_pricing_for_new_patient', 'N/A'),
                        "max_pricing": record.get('max_medicare_pricing_for_new_patient', 'N/A')
                    })
                else:
                    formatted_results.append({
                        "zip_code": record.get('zip_code', 'N/A'),
                        "min_pricing": record.get('min_medicare_pricing_for_established_patient', 'N/A'),
                        "max_pricing": record.get('max_medicare_pricing_for_established_patient', 'N/A')
                    })

            return jsonify(formatted_results)

        return jsonify({"error": "Failed to fetch data from CMS API"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
