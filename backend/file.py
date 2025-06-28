#creating json file that user downloads

import json

def create_file(coordinates):
    data = {
        'name': 'GeoTrainr Map',
        'customCoordinates': []
    }

    for coordinate in coordinates:
        parsed_coords = {"lat": coordinate[1], "lng": coordinate[0]}
        data['customCoordinates'].append(parsed_coords)

    with open('output.json', 'w') as f:
        json.dump(data, f, indent=4)
