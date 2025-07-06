import os
import csv
import requests
import tempfile
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from gradio_client import Client, handle_file
from dotenv import load_dotenv


load_dotenv()
ACCESS_TOKEN=os.environ.get('ACCESS_TOKEN')
LIMIT = 500
HF_SPACE_ID = "evanss2025/geotrainr-model"
HF_CLIENT = Client(HF_SPACE_ID)

MAX_WORKERS = 8
BATCH_SIZE = 128

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

def send_to_inference(img_url, coords):
    try:
        img_bytes = requests.get(img_url).content
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_bytes)
            tmp.flush()
            result = HF_CLIENT.predict(
                image=handle_file(tmp.name),
                api_name="/predict"
            )
            if result:
                logging.info("✅ Detection found")
                return coords
    except Exception as e:
        logging.error(f"❌ Error calling HF Space inference: {e}")
    return None

def run_inference(country):
    logging.info(f"✅ Running inference for country: {country}")
    bbox = read_csv(country)
    url = f"https://graph.mapillary.com/images?fields=id,thumb_2048_url,geometry&bbox={bbox}&limit={LIMIT}&access_token={ACCESS_TOKEN}"

    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json().get("data", [])
    except Exception as e:
        logging.error(f"❌ Failed to fetch images from Mapillary: {e}")
        return []

    logging.debug(f"🧭 Got {len(data)} images from Mapillary")
    filtered_coords = []

    # Split data into batches
    batches = [data[i:i+BATCH_SIZE] for i in range(0, len(data), BATCH_SIZE)]

    for batch in batches:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(send_to_inference, item['thumb_2048_url'], item['geometry']['coordinates'])
                for item in batch if 'thumb_2048_url' in item
            ]
            for future in as_completed(futures):
                coords = future.result()
                if coords:
                    filtered_coords.append(coords)

    logging.info(f"📦 Total detections: {len(filtered_coords)} / {len(data)}")
    return filtered_coords