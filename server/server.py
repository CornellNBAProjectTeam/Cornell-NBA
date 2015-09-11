from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Index page of Cornell NBA Prediction Project API."

@app.route("/stats")
def get_stats():
    return "Get stats"

if __name__ == "__main__":
    app.run()
