#creating json file that user downloads

import json, io
from io import BytesIO

def create_file(coordinates):
    data = {
        'name': 'GeoTrainr Map',
        'customCoordinates': []
    }

    for coordinate in coordinates:
        parsed_coords = {"lat": coordinate[1], "lng": coordinate[0]}
        data['customCoordinates'].append(parsed_coords)

    json_string = json.dumps(data, indent=4)

    return io.BytesIO(json_string.encode('utf-8'))
