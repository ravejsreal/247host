from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import subprocess
import os
import threading

app = Flask(__name__)

# Directory to store the uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Variable to hold the process
python_process = None

@app.route('/')
def index():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Run the Python file in a separate thread
    def run_script():
        global python_process
        python_process = subprocess.Popen(['python', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in python_process.stdout:
            print(line.decode('utf-8'), end='')

    threading.Thread(target=run_script).start()

    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_script():
    global python_process
    if python_process:
        python_process.terminate()
        python_process = None

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
