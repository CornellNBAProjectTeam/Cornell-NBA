from flask import Flask
import os
from espnGameScraper import generateJSONData

app = Flask(__name__)

@app.route("/")
def hello():
    return "Index page of Cornell NBA Prediction Project API."

@app.route("/prediction")
def prediction():
	return generateJSONData()

@app.route("/update")
def update():
	# UPDATE SERVER DATA
	return json.dumps({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
