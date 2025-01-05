import os
import subprocess
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api')
def home():
    return jsonify(message="API is up and running!")

@app.route('/run-provocis', methods=['POST'])
def run_provocis():
    try:
        # Path to the uploaded file
        file_path = os.path.join('uploads', 'provocis.py')

        if os.path.exists(file_path):
            # Run the provocis.py file (assuming it does not require a specific Python environment)
            result = subprocess.run(['python', file_path], capture_output=True, text=True)

            if result.returncode == 0:
                return jsonify(message="File executed successfully!", output=result.stdout)
            else:
                return jsonify(message="Error executing file", error=result.stderr)
        else:
            return jsonify(message="File 'provocis.py' not found in uploads folder"), 404
    except Exception as e:
        return jsonify(message=f"An error occurred: {str(e)}"), 500

if __name__ == "__main__":
    app.run()
