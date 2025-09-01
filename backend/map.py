import os
import csv
import time
import logging
import tempfile
import requests
from dotenv import load_dotenv
from gradio_client import Client, handle_file
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from progress import progress_status

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
LIMIT = 50 
MAX_WORKERS = 2
TIMEOUT = 30
HF_CLIENT = Client("evanss2025/geotrainr-model")
HF_API_NAME = "/predict"

def read_csv(country):
    logging.info(f"📍 Reading bounding box for country: {country}")
    with open('country-boundingboxes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == country:
                longmin, latmin, longmax, latmax = row[1:5]
                return f"{longmin},{latmin},{longmax},{latmax}"
    return "0,0,0,0"

def validate_access_token():
    if not ACCESS_TOKEN:
        logger.error("❌ ACCESS_TOKEN not found in environment variables")
        return False
    
    test_url = "https://graph.mapillary.com/images"
    test_params = {
        'fields': 'id',
        'limit': 1,
        'bbox': '2.0,48.0,3.0,49.0',
        'access_token': ACCESS_TOKEN
    }
    
    try:
        response = requests.get(test_url, params=test_params, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Access token is valid")
            return True
        else:
            logger.error(f"❌ Access token validation failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error validating access token: {e}")
        return False

def split_bbox(bbox_str, max_area=5.0):
    parts = bbox_str.split(',')
    west, south, east, north = map(float, parts)
    
    area = (east - west) * (north - south)
    
    logger.info(f"📏 Bbox area: {area:.2f} square degrees")
    
    if area <= max_area:
        return [bbox_str]
    
    # Recursively split until all segments are small enough
    def recursive_split(w, s, e, n):
        current_area = (e - w) * (n - s)
        if current_area <= max_area:
            return [f"{w},{s},{e},{n}"]
        
        # Split the larger dimension
        width = e - w
        height = n - s
        
        segments = []
        if width > height:
            # Split horizontally
            mid_lon = (w + e) / 2
            segments.extend(recursive_split(w, s, mid_lon, n))
            segments.extend(recursive_split(mid_lon, s, e, n))
        else:
            # Split vertically
            mid_lat = (s + n) / 2
            segments.extend(recursive_split(w, s, e, mid_lat))
            segments.extend(recursive_split(w, mid_lat, e, n))
        
        return segments
    
    segments = recursive_split(west, south, east, north)
    logger.info(f"📦 Split large bbox into {len(segments)} smaller segments")
    return segments

def fetch_mapillary_images(bbox):
    
    if not validate_access_token():
        return []
    
    all_images = []
    current_url = "https://graph.mapillary.com/images"
    max_pages = 4

    
    params = {
        'fields': 'id,thumb_2048_url,geometry',
        'bbox': bbox,
        'limit': 50,
        'access_token': ACCESS_TOKEN
    }
    
    logger.info(f"🔍 Fetching images for bbox: {bbox} (up to {max_pages} pages)")
    
    for page_num in range(max_pages):
        progress_status["phase"] = f"Fetching page {page_num + 1}/{max_pages} from Mapillary..."
        
        try:
            if page_num == 0:
                response = requests.get(current_url, params=params, timeout=30)
            else:
                response = requests.get(current_url, timeout=30)
            
            logger.info(f"📊 Page {page_num + 1} - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                page_images = data.get('data', [])
                all_images.extend(page_images)
                
                logger.info(f"✅ Page {page_num + 1}: Got {len(page_images)} images")
                logger.info(f"📊 Total images so far: {len(all_images)}")
                
                paging = data.get('paging', {})
                next_url = paging.get('next')
                
                if not next_url:
                    logger.info("🏁 No more pages available")
                    break
                
                current_url = next_url
                
            elif response.status_code == 400:
                logger.error(f"❌ Bad Request on page {page_num + 1}: {response.text}")
                break
            elif response.status_code == 401:
                logger.error(f"❌ Unauthorized on page {page_num + 1}: Check access token")
                break
            elif response.status_code == 429:
                logger.warning(f"⚠️ Rate limited on page {page_num + 1}, waiting...")
                time.sleep(30)
                continue
            else:
                logger.warning(f"⚠️ Unexpected status {response.status_code} on page {page_num + 1}")
                break
                        
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Page {page_num + 1} timed out")
            break
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching page {page_num + 1}: {e}")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error on page {page_num + 1}: {e}")
            break
    
    logger.info(f"🎯 Total images collected: {len(all_images)} from {page_num + 1} pages")
    return all_images

def process_image(item):
    try:
        img_url = item.get('thumb_2048_url')
        if not img_url:
            logger.warning("⚠️ No thumbnail URL found, skipping")
            return None

        coords = item['geometry']['coordinates']
        
        img_response = requests.get(img_url, timeout=30)
        img_response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_file.write(img_response.content)
            tmp_path = tmp_file.name
        
        try:
            result = HF_CLIENT.predict(
                image=handle_file(tmp_path),
                api_name=HF_API_NAME
            )
            
            if result:
                logger.info("✅ Detection found")
                return coords
            else:
                logger.debug("ℹ️ No detections")
                return None
                
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass
            
    except Exception as e:
        logger.error(f"❌ Error processing image: {e}")
        return None

def run_inference(country):
    logger.info(f"✅ Running inference for country: {country}")
    
    bbox = read_csv(country)
    if bbox == "0,0,0,0":
        logger.error(f"❌ No bounding box found for country: {country}")
        return []
    
    bbox_list = split_bbox(bbox)
    
    progress_status["phase"] = "Fetching Images..."
    progress_status["processed_images"] = 0
    progress_status["total_images"] = 0
    
    all_image_data = []
    MAX_TOTAL_IMAGES = 50
    
        # Fetch images from all bbox segments
    for i, bbox_segment in enumerate(bbox_list):
        logger.info(f"📦 Processing bbox segment {i+1}/{len(bbox_list)}: {bbox_segment}")
        
        # Check if we've reached our limit
        if len(all_image_data) >= MAX_TOTAL_IMAGES:
            logger.info(f"🎯 Reached maximum image limit of {MAX_TOTAL_IMAGES}")
            break
        
        progress_status["phase"] = f"Fetching images from segment {i+1}/{len(bbox_list)}"
        
        image_data = fetch_mapillary_images(bbox_segment)
        if image_data:
            # Only add images up to our limit
            remaining_slots = MAX_TOTAL_IMAGES - len(all_image_data)
            images_to_add = image_data[:remaining_slots]
            all_image_data.extend(images_to_add)
            
            logger.info(f"✅ Added {len(images_to_add)} images from segment {i+1} (total: {len(all_image_data)})")
            
            if len(all_image_data) >= MAX_TOTAL_IMAGES:
                logger.info(f"🎯 Reached maximum image limit of {MAX_TOTAL_IMAGES}")
                break
        else:
            logger.warning(f"⚠️ No images from segment {i+1}")
        
        # Longer delay between requests to avoid rate limiting
        if i < len(bbox_list) - 1:
            logger.info(f"⏳ Waiting 5 seconds before next segment...")
            time.sleep(0.5)
    
    if not all_image_data:
        logger.warning("⚠️ No images found for this country")
        return []
    
    filtered_map_coords = []
    progress_status["phase"] = "Running images through model..."
    progress_status["total_images"] = len(all_image_data)
    
    # Process images with thread pool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_image, item): item for item in all_image_data}
        
        for future in as_completed(futures, timeout=LIMIT * TIMEOUT):
            try:
                result = future.result(timeout=TIMEOUT)
                if result:
                    filtered_map_coords.append(result)
                progress_status["processed_images"] += 1
                
            except TimeoutError:
                logger.warning("⏳ Image processing timed out and was skipped")
                progress_status["processed_images"] += 1
            except Exception as e:
                logger.error(f"⚠️ Future failed: {e}")
                progress_status["processed_images"] += 1
    
    progress_status["phase"] = "done"
    logger.info(f"🎯 Total detections: {len(filtered_map_coords)} / {len(all_image_data)}")
    return filtered_map_coords
