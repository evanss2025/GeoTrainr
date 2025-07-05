import os
import requests
import csv
import logging
import base64

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
LIMIT = 50

HF_SPACE_INFERENCE_URL = "https://geotrainr-model-evanss2025.hf.space/run/predict"

if not ACCESS_TOKEN:
    logger.warning("⚠️ ACCESS_TOKEN not set")

def read_csv(country):
    logger.info("📍 Reading bounding box for country: %s", country)
    try:
        with open('country-boundingboxes.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0] == country:
                    longmin = row[1]
                    latmin = row[2]
                    longmax = row[3]
                    latmax = row[4]
                    return f"{longmin},{latmin},{longmax},{latmax}"
    except Exception as e:
        logger.error("❌ Error reading CSV: %s", e)
    return "0,0,0,0"

def run_inference(country):
    logger.info("✅ Running inference for country: %s", country)

    bbox = read_csv(country)
    url = f"https://graph.mapillary.com/images?fields=id,thumb_2048_url,geometry&bbox={bbox}&limit={LIMIT}&access_token={ACCESS_TOKEN}"

    try:
        res = requests.get(url).json().get("data", [])
    except Exception as e:
        logger.error("❌ Error fetching Mapillary data: %s", e)
        return []

    logger.debug("🧭 Got %d images from Mapillary", len(res))

    filtered_map_coords = []

    for item in res:
        img_url = item.get('thumb_2048_url')
        if not img_url:
            continue

        coords = item['geometry']['coordinates']

        # Download image
        try:
            img_bytes = requests.get(img_url).content
        except Exception as e:
            logger.error("❌ Error downloading image: %s", e)
            continue

        # Encode to base64 for HF input
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{img_b64}"

        payload = {
            "data": [{
                "url": data_url,
                "mime_type": "image/jpeg",
                "orig_name": "image.jpg",
                "is_stream": False,
                "meta": {}
            }]
        }

        # Send to HF Space
        try:
            response = requests.post(HF_SPACE_INFERENCE_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.debug("🧪 HF Response: %s", result)
        except Exception as e:
            logger.error("❌ Error calling HF Space: %s", e)
            continue

        # Check for detections
        detections = result.get('data', [{}])[0].get('value', [])
        if detections:
            filtered_map_coords.append(coords)
            logger.info("✅ Detection found. Added coords.")
        else:
            logger.info("🚫 No detection in image.")

    logger.info("📦 Total detections: %d / %d", len(filtered_map_coords), len(res))
    return filtered_map_coords