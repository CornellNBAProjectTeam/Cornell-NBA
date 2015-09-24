from flask import Flask
import os

app = Flask(__name__)

# Environment Variables
ACCOUNT_USER = os.environ.get('MONGOLAB_USERNAME')
ACCOUNT_PASS = os.environ.get('MONGOLAB_PASS')
DB_NAME = os.environ.get('MONGO_DB_NAME')
DB_USER = os.environ.get('MONGO_DB_USER')
DB_PASS = os.environ.get('MONGO_DB_PASS')

@app.route("/")
def hello():
    return "Index page of Cornell NBA Prediction Project API."

@app.route("/stats")
def get_stats():
    return "Get stats"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
