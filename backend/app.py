from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
import traceback
from geospatial_analysis import start_automation
from flasgger import Swagger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
swagger = Swagger(app)
CORS(app)

@app.route('/', methods=['GET'])
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Error serving index.html: {str(e)}")
        return jsonify({'message': 'Failed to load dashboard'}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        print("Received POST to /api/analyze")
        print(f"Form data: {dict(request.form)}")
        if 'file' in request.files:
            print(f"File: {request.files['file'].filename}")
        else:
            print("No file in request")

        if 'file' not in request.files or not request.files['file'].filename:
            return jsonify({'message': 'No file uploaded or invalid file','status':400}), 400
        
        file = request.files['file']
        start_date = request.form.get('startDate')
        end_date = request.form.get('endDate')
        satellite = request.form.get('satellite')
        cloud_percentage = request.form.get('cloudPercentage')
        indices = request.form.get('indices', [])

        if not all([start_date, end_date, satellite, cloud_percentage, indices]):
            print("Missing form fields")
            return jsonify({'message': 'Missing required form fields' ,'status':400}), 400

        try:
            cloud_percentage = int(cloud_percentage)
            indices = json.loads(indices)
        except ValueError as ve:
            print(f"Invalid form data: {str(ve)}")
            return jsonify({'message': f'Invalid form data: {str(ve)}' ,'status':400}), 400

        os.makedirs('uploads', exist_ok=True)
        file_path = os.path.join('uploads', file.filename)
        print(f"Saving file to: {file_path}")
        file.save(file_path)

        if not os.path.exists(file_path):
            print(f"File not saved: {file_path}")
            return jsonify({'message': 'Failed to save uploaded file','status':500}), 500

        print("Calling start_automation")
        result = start_automation(
            file_path=file_path,
            start_date=start_date,
            end_date=end_date,
            satellite=satellite,
            cloud_percentage=cloud_percentage,
            indices=indices
        )

        result_json = json.loads(result)

        # if os.path.exists(file_path):
        #     os.remove(file_path)
        #     print(f"Removed file: {file_path}")

        return jsonify({"message": "Analysis complete", "data": result_json, 'status':200}),200
    
    except Exception as e:
        print(f"Error in /api/analyze: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'message': f'Internal server message: {str(e)}'}), 500

if __name__ == '__main__':
    # app.run(debug=True, port=8000)
    app.run(debug=True, host="0.0.0.0", port=8000)