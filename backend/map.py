import os
import csv
import requests
import tempfile
import logging
from gradio_client import Client, handle_file

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
LIMIT = 50
HF_SPACE_ID = "evanss2025/geotrainr-model"
HF_CLIENT = Client(HF_SPACE_ID)

logging.basicConfig(level=logging.INFO)

def read_csv(country):
    logging.info(f"📍 Reading bounding box for country: {country}")
    with open('country-boundingboxes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == country:
                longmin, latmin, longmax, latmax = row[1:5]
                return f"{longmin},{latmin},{longmax},{latmax}"
    return "0,0,0,0"

def send_to_inference(img_url):
    try:
        img_bytes = requests.get(img_url).content
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_bytes)
            tmp.flush()
            result = HF_CLIENT.predict(
                image=handle_file(tmp.name),
                api_name="/predict"
            )
            return result
    except Exception as e:
        logging.error(f"❌ Error calling HF Space inference: {e}")
        return []

def run_inference(country):
    logging.info(f"✅ Running inference for country: {country}")
    bbox = read_csv(country)
    url = f"https://graph.mapillary.com/images?fields=id,thumb_2048_url,geometry&bbox={bbox}&limit={LIMIT}&access_token={'MLY|24655495800719206|1dc830c67e92179b3d860ab1f9a37336'}"

    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json().get("data", [])
    except Exception as e:
        logging.error(f"❌ Failed to fetch images from Mapillary: {e}")
        return []

    logging.debug(f"🧭 Got {len(data)} images from Mapillary")
    filtered_map_coords = []

    for item in data:
        img_url = item.get("thumb_2048_url")
        if not img_url:
            continue

        coords = item["geometry"]["coordinates"]
        detections = send_to_inference(img_url)
        
        if detections:
            filtered_map_coords.append(coords)
            logging.info("✅ Detection found, coords added")
        else:
            logging.info("No detections")

    logging.info(f"📦 Total detections: {len(filtered_map_coords)} / {len(data)}")
    return filtered_map_coords
