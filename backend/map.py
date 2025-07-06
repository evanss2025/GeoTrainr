import os
import requests
import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from gradio_client import Client, handle_file
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
LIMIT = 500
MAX_WORKERS = 8
HF_CLIENT = Client("evanss2025/geotrainr-model")
HF_API_NAME = "/predict"


def read_csv(country):
    logger.info(f"📍 Reading bounding box for country: {country}")
    with open('country-boundingboxes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == country:
                return f"{row[1]},{row[2]},{row[3]},{row[4]}"
    return "0,0,0,0"


def fetch_mapillary_images(bbox):
    url = (
        f"https://graph.mapillary.com/images"
        f"?fields=id,thumb_2048_url,geometry"
        f"&bbox={bbox}&limit={LIMIT}&access_token={ACCESS_TOKEN}"
    )
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json().get("data", [])
        logger.debug(f"🧭 Got {len(data)} images from Mapillary")
        return data
    except Exception as e:
        logger.error(f"❌ Failed to fetch images from Mapillary: {e}")
        return []


def process_image(item):
    try:
        img_url = item.get('thumb_2048_url')
        if not img_url:
            logger.warning("⚠️ No thumbnail URL found. Skipping.")
            return None

        coords = item['geometry']['coordinates']
        try:
            img_res = requests.get(img_url, timeout=10)
            img_res.raise_for_status()
            img_bytes = img_res.content
        except Exception as e:
            logger.warning(f"⚠️ Skipping image due to download error: {e}")
            return None

        try:
            result = HF_CLIENT.predict(
                image=handle_file(img_bytes),
                api_name=HF_API_NAME
            )
        except KeyError as e:
            logger.warning(f"⚠️ GradioClient KeyError during prediction: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error during HF prediction: {e}")
            return None

        if result:
            logger.info("✅ Detection found")
            return coords
        else:
            logger.info("No detections")
            return None

    except Exception as e:
        logger.error(f"❌ Error processing image: {e}")
        return None


def run_inference(country):
    logger.info(f"✅ Running inference for country: {country}")
    bbox = read_csv(country)
    image_data = fetch_mapillary_images(bbox)

    filtered_map_coords = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_image, item) for item in image_data]
        for future in as_completed(futures):
            try:
                result = future.result(timeout=30)  # Timeout per image processing
                if result:
                    filtered_map_coords.append(result)
            except TimeoutError:
                logger.warning("⚠️ Image processing timed out. Skipping.")
            except Exception as e:
                logger.warning(f"⚠️ Skipping due to error: {e}")

    logger.info(f"📦 Total detections: {len(filtered_map_coords)} / {len(image_data)}")
    return filtered_map_coords
