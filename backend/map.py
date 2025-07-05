import os
import requests
import csv

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
LIMIT = 50

HF_SPACE_INFERENCE_URL = "https://geotrainr-model-evanss2025.hf.space/run/predict"

def read_csv(country):
    with open('country-boundingboxes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == country:
                longmin = row[1]
                latmin = row[2]
                longmax = row[3]
                latmax = row[4]
                return f"{longmin},{latmin},{longmax},{latmax}"
        return 0, 0, 0, 0

def run_inference(country):
    print("✅ Running inference via HF Space API")
    
    url = f"https://graph.mapillary.com/images?fields=id,thumb_2048_url,geometry&bbox={read_csv(country)}&limit={LIMIT}&access_token={ACCESS_TOKEN}"
    res = requests.get(url).json().get("data", [])

    filtered_map_coords = []

    for item in res:
        img_url = item.get('thumb_2048_url')
        if not img_url:
            continue
        
        coords = item['geometry']['coordinates']
        
        # Download image bytes
        try:
            img_bytes = requests.get(img_url).content
        except Exception as e:
            print("Error downloading image:", e)
            continue
        
        # Send image bytes to HF Space inference API
        files = {"image": ("image.jpg", img_bytes, "image/jpeg")}
        try:
            response = requests.post(HF_SPACE_INFERENCE_URL, files=files)
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            print("Error calling HF Space inference:", e)
            continue
        
        # Check if any detections found (adjust based on your HF output format)
        # Assuming result is a JSON string of pandas output or similar
        detections = result.get('data', [{}])[0].get('value', [])
        if detections:  # if any detections exist, keep coords
            filtered_map_coords.append(coords)
            print("✅ Detection found, coords added")
        else:
            print("No detections")

    print(f"Total detections: {len(filtered_map_coords)} / {len(res)}")
    return filtered_map_coords