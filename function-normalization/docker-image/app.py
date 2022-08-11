# Import custom Libraries
from tools import normalize
# Libraries 
import os
from flask import Flask, request, Response, make_response, jsonify

""" Environment Variables """
# Flask app Host and Port
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", 5000))

""" Global variables """
# The name of the Flask app
app = Flask(__name__)

""" Flask endpoints """
# Normalization route
@app.route("/normalize", methods=["POST"])
def analysis():
    # Get Complex JSON
    print("[INFO] Accepted Request.")
    complex_func = request.json

    # Return the normalized JSON
    return jsonify(normalize(complex_func))

""" Main """
# Main code
if __name__ == "__main__":
    app.run(HOST, PORT, True)