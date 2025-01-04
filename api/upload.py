import json

def handler(request):
    # Check if the method is POST
    if request.method == "POST":
        try:
            # Handle the POST request here
            data = request.json()  # If you're using Flask or handling the body here
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Request received", "data": data})
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }
    else:
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"})
        }
