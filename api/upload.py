import subprocess
import os

def handler(request):
    # Extract the file from the request and save it temporarily
    file = request.files['file']
    filename = f"/tmp/{file.filename}"
    file.save(filename)

    # Run the uploaded Python file (this will only run during the request)
    try:
        process = subprocess.Popen(['python', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        output = stdout.decode() if process.returncode == 0 else stderr.decode()

        # Return the output or error as a response
        return {
            "statusCode": 200,
            "body": output
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error running the bot: {str(e)}"
        }
