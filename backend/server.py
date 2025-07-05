from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, sys

sys.path.append("yolov5")

from map import read_csv, model
from file import create_file

app = Flask(__name__)
CORS(app)

@app.route("/", methods=['POST', 'GET'])
def submit():
    if request.method == "OPTIONS":
        return jsonify({'status': 'ok'}), 200  # Respond to preflight
    
    parsed_data = []
    data = request.get_json()
    weaknesses = data.get('userWeaknesses', [])

    print(weaknesses)

    for weakness in weaknesses:
        parsed_data += model(weakness.get('country'))

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

