import io, PIL
from dotenv import load_dotenv
import os, requests, csv
from PIL import Image
from io import BytesIO
import numpy as np
import torch
from pathlib import Path
from models.common import DetectMultiBackend
from utils.general import non_max_suppression
from utils.torch_utils import select_device
from concurrent.futures import ThreadPoolExecutor

load_dotenv()  # take environment variables

def read_csv(country):
    with open('country-boundingboxes.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == country:
                print("FOUND", country)
                longmin = row[1]
                latmin = row[2]
                longmax = row[3]
                latmax = row[4]

                print(longmin, latmin, longmax, latmax)

                return f"{longmin},{latmin},{longmax},{latmax}"
            # else:
            #     print("NOT FOUND")

        return 0, 0, 0, 0

ACCESS_TOKEN=os.environ.get('ACCESS_TOKEN')
LIMIT = 500

def get_img(item):
    try:
        img_url = item.get('thumb_2048_url')
        if img_url is None:
            print('NO URL')
            return None
        
        coords = item['geometry']['coordinates']

        img_data = requests.get(img_url).content
        img_data = io.BytesIO(img_data)

        return img_data, coords
    
    except Exception as e:
        print("error downloading")
        return None


def model(country):
    print("✅ model function running")
    url = f"https://graph.mapillary.com/images?fields=id,thumb_2048_url,geometry&bbox={read_csv(country)}&limit={LIMIT}&access_token={ACCESS_TOKEN}"
    res = requests.get(url).json().get("data", [])

    image_paths=[]
    map_coords = []
    filtered_map_coords = []

    #this part works correctly for now
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_img, res))

    for result in results:
        if result is None:
            continue
        img_data, coords = result
        image_paths.append(img_data)
        map_coords.append(coords)

        print(f"✅ downloaded {len(image_paths)} images")

    weights_path = 'yolov5/best.pt'
    device = select_device('') 
    model = DetectMultiBackend(weights_path, device=device)
    model.eval()

    batch_size = 32
    img_tensors = []
    
    for i, path in enumerate(image_paths):
        try:
            img = PIL.Image.open(path).convert("RGB")
        except PIL.UnidentifiedImageError:
            print("Skipping invalid image")
            continue
        img_resized = img.resize((640, 640))
        img_array = np.array(img_resized)

        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        # img_tensor = img_tensor.to(device)
        img_tensors.append(img_tensor)

    for i in range(0, len(img_tensors), batch_size):
        batch = torch.cat(img_tensors[i:i+batch_size], dim=0).to(device)

        print(f"batch {i // batch_size + 1} with size {batch.shape[0]}")

        pred = model(batch)
        detections = non_max_suppression(pred)

        for j, det in enumerate(detections):
            if det is not None and len(det):
                filtered_map_coords.append(map_coords[i + j])
                print("✅ bollard found, coords added")
            else:
                print("NOTHING DETECTED")

    print(f"Total detections: {len(filtered_map_coords)} / {len(map_coords)}")
    return filtered_map_coords
