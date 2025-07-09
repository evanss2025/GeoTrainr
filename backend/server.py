from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, sys

from map import read_csv, run_inference
from file import create_file

app = Flask(__name__)
CORS(app, origins=["https://geotrainr.vercel.app"])

@app.route("/", methods=['POST', 'GET', 'OPTIONS'])
def submit():
    if request.method == "OPTIONS":
        return jsonify({'status': 'ok'}), 200  # Respond to preflight

    parsed_data = []
    data = request.get_json()
    weaknesses = data.get('userWeaknesses', [])

    print("Received countries:", [w.get('country') for w in weaknesses])

    for weakness in weaknesses:
        parsed_data += run_inference(weakness.get('country'))

    json_file = create_file(parsed_data)
    json_file.seek(0)

    return send_file(
        json_file,
        mimetype='application/json',
        as_attachment=True,
        download_name='GeoTrainr-Map.json'
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
