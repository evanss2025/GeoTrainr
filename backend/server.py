from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys

sys.path.append("yolov5")

from map import read_csv, model
from file import create_file

app = Flask(__name__)
CORS(app)

@app.route("/", methods=['POST', 'GET'])
def submit():
    if request.method == "POST":
        parsed_data = []
        data = request.get_json()
        weaknesses = data.get('userWeaknesses')

        print(weaknesses)

        for weakness in weaknesses:
            parsed_data += model(weakness.get('country'))

        create_file(parsed_data)
        
    return 'received'


if __name__ == '__main__':
    app.run(debug=True, port=8080)

