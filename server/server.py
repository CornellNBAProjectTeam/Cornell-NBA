from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Index page of Cornell NBA Prediction Project API."

@app.route("/stats")
def get_stats():
    return "Get stats"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
