import requests
import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor

api_key = '5aCK45kUAtTDgETwclKks07q2W3bi5XA0nJ2Zm0W'
api_url = 'https://api.nasa.gov/mars-photos/api/v1/rovers/'

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_rover_data():
    try:
        r = requests.get(api_url + '?api_key=' + api_key)
        r.raise_for_status()  # Raise an error for bad status codes
        return r.json()
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve rover data: {e}")
        sys.exit(1)

def get_photos(rover, sol, camera):
    sol_pic = False
    retry_count = 0

    while not sol_pic:
        try:
            r = requests.get(f"{api_url}{rover}/photos?sol={sol}&camera={camera}&api_key={api_key}")
            r.raise_for_status()
            data = r.json()

            if data['photos'] or retry_count > 2:
                sol_pic = True
            else:
                sol -= 1
                retry_count += 1

        except requests.RequestException as e:
            logging.error(f"Error fetching photos for {rover} on Sol {sol} with camera {camera}: {e}")
            return []

    return data['photos']

def download_photo(photo_url, file_path):
    try:
        img_data = requests.get(photo_url).content
        with open(file_path, 'wb') as handler:
            handler.write(img_data)
        logging.info(f"Downloaded {file_path}")
    except requests.RequestException as e:
        logging.error(f"Failed to download image from {photo_url}: {e}")

def download_photos(camera_data, camera_name, path):
    last_photo_url = camera_data[-1]['img_src']
    file_path = os.path.join(path, f"{camera_name}.jpg")
    download_photo(last_photo_url, file_path)

def main():
    rover_data = get_rover_data()
    path = 'frontend/images/'
    if not os.path.exists(path):
        os.makedirs(path)

    with ThreadPoolExecutor(max_workers=4) as executor:
        for rover in rover_data['rovers']:
            rover_path = os.path.join(path, rover['name'])
            if not os.path.exists(rover_path):
                os.makedirs(rover_path)

            if rover['status'] == 'complete':
                logging.info(f"Skipping rover {rover['name']} (status: {rover['status']})")
                continue

            logging.info(f"Scraping rover {rover['name']}, starting with Sol {rover['max_sol']}")

            for camera in rover['cameras']:
                logging.info(f"Scraping camera {rover['name']}@{camera['name']} ({camera['full_name']})")
                camera_data = get_photos(rover['name'], rover['max_sol'], camera['name'])
                if not camera_data:
                    continue

                file_name = f"{rover['name']}_{camera['name']}.jpg"
                file_path = os.path.join(rover_path, file_name)
                executor.submit(download_photo, camera_data[-1]['img_src'], file_path)

if __name__ == '__main__':
    main()