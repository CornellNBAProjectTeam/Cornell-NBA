from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Index page of Cornell NBA Prediction Project API."

if __name__ == "__main__":
    app.run()
