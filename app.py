from flask import Flask, render_template_string, request, jsonify, Response
import subprocess
import os

app = Flask(__name__)

running_process = None
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# HTML template embedded in the Python file (index.html part)
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
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>Python Code Executor</h1>
        <input type="file" id="fileInput">
        <button id="uploadButton">Upload File</button>
        <button id="runButton">Run Code</button>
        <button id="stopButton">Stop Execution</button>
        
        <h2>Output:</h2>
        <div id="output">Waiting for output...</div>
    </div>
    
    <script>
        $('#uploadButton').click(function() {
            var file = $('#fileInput')[0].files[0];
            var formData = new FormData();
            formData.append('file', file);
            $.ajax({
                url: '/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    alert(response.message);
                }
            });
        });

        $('#runButton').click(function() {
            var filename = $('#fileInput')[0].files[0].name;
            $.ajax({
                url: '/run',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({filename: filename}),
                success: function(response) {
                    $('#output').text(response.output);
                }
            });
        });

        $('#stopButton').click(function() {
            $.ajax({
                url: '/stop',
                type: 'POST',
                success: function(response) {
                    alert(response.message);
                }
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(html_content)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return jsonify({'message': 'File uploaded successfully'})

@app.route('/run', methods=['POST'])
def run_code_route():
    global running_process
    if running_process is None or running_process.poll() is not None:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], request.json['filename'])
        return Response(run_code(file_path), mimetype='text/plain')
    else:
        return jsonify({'message': 'Code is already running'})

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
            print(f"STDOUT: {stdout_line.strip()}")  # Output to console
            yield stdout_line
        if stderr_line:
            print(f"STDERR: {stderr_line.strip()}")  # Output to console
            yield stderr_line
        
        # End of process
        if stdout_line == '' and stderr_line == '' and running_process.poll() is not None:
            break

    running_process.stdout.close()
    running_process.stderr.close()
    running_process.wait()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
