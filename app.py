import os
import subprocess
from flask import Flask, render_template_string, jsonify, Response
import sys

app = Flask(__name__)

# Define upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# HTML template for the frontend
html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Code Executor</title>
    <style>
        body {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            margin: 0;
            padding: 0;
        }
        h1 {
            font-size: 3rem;
            color: #FFD700;
            margin-top: 50px;
            font-weight: 700;
        }
        button {
            margin: 15px;
            padding: 15px;
            font-size: 16px;
            cursor: pointer;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #45a049;
        }
        #output {
            white-space: pre-wrap;
            text-align: left;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: scroll;
            width: 80%;
            margin: auto;
            padding: 10px;
            background-color: #333;
            border-radius: 8px;
            color: #ddd;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }
        input[type="file"] {
            margin: 20px;
            font-size: 18px;
        }
        .container {
            text-align: center;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Python Code Executor</h1>
        
        <h2>Output:</h2>
        <div id="output">Waiting for output...</div>
    </div>
    
    <script>
        // Automatically trigger the 'run' route when the page loads
        window.onload = function() {
            fetch('/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('output').innerText = data.output;
            })
            .catch(error => {
                console.error('Error:', error);
            });
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(html_content)

@app.route('/run', methods=['POST'])
def run_code_route():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'provocis.py')

    if os.path.exists(file_path):
        return Response(run_code(file_path), mimetype='text/plain')
    else:
        return jsonify({'message': 'provocis.py file not found in the uploads folder.'})

@app.route('/stop', methods=['POST'])
def stop_code():
    global running_process
    if running_process:
        running_process.terminate()
        return jsonify({'message': 'Execution stopped'})
    else:
        return jsonify({'message': 'No process is running'})

# Run the code in a separate thread and stream output
def run_code(file_path):
    global running_process
    output = ""

    # Start the process
    running_process = subprocess.Popen(
        ['python', file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True
    )

    # Stream the output in real-time to the browser
    while True:
        stdout_line = running_process.stdout.readline()
        stderr_line = running_process.stderr.readline()
        
        if stdout_line:
            output += stdout_line.strip() + '\n'
        if stderr_line:
            output += stderr_line.strip() + '\n'
        
        # End of process
        if stdout_line == '' and stderr_line == '' and running_process.poll() is not None:
            break

    running_process.stdout.close()
    running_process.stderr.close()
    running_process.wait()
    
    return jsonify({'output': output})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
