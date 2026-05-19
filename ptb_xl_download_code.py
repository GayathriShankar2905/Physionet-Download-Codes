pip install wfdb

import os
import requests
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

# PhysioNet Credentials
PHYSIONET_USERNAME = "pcmjs-gayathri"
PHYSIONET_API_KEY = "parabola29052005"

# Save dataset to Desktop in "ptb_xl_dataset" folder
DEST_DIR = r"D:\ptb-xl"
os.makedirs(DEST_DIR, exist_ok=True)

# Base URL for PTB-XL dataset (training)
BASE_URL = "https://physionet.org/files/challenge-2021/1.0.3/training/ptb-xl/"

# Initialize session with authentication
session = requests.Session()
session.auth = (PHYSIONET_USERNAME, PHYSIONET_API_KEY)
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 30
MAX_RETRIES = 5

# Function to make GET requests with retries
def make_request(url):
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            if response.status_code == 200:
                return response
            print(f"⚠️ Attempt {attempt + 1}: Received status {response.status_code}. Retrying...")
        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt + 1}: Connection failed: {e}. Retrying...")
        
        time.sleep(2 ** attempt)  # Exponential backoff

    print(f"🚨 Failed to retrieve {url} after {MAX_RETRIES} attempts.")
    return None

# Function to get list of subdirectories (g1/, g2/, ..., g22/)
def get_subdirectories():
    response = make_request(BASE_URL)
    if not response:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    subdirs = [a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith("/")]
    return subdirs

# Function to get list of files in a subdirectory
def get_file_list(subdir):
    subdir_url = BASE_URL + subdir
    response = make_request(subdir_url)
    if not response:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    files = [subdir + a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith((".hea", ".mat", ".csv"))]
    return files

# Function to download a file
def download_file(filename):
    url = BASE_URL + filename
    dest_path = os.path.join(DEST_DIR, filename.replace("/", "_"))  # Replace '/' to avoid folder creation issues

    if os.path.exists(dest_path):
        print(f"✅ File {filename} already exists. Skipping...")
        return

    response = make_request(url)
    if response and response.status_code == 200:
        file_size = int(response.headers.get("Content-Length", 0))
        with open(dest_path, "wb") as file, tqdm(
            total=file_size, unit="B", unit_scale=True, desc=f"Downloading {filename}"
        ) as progress:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    progress.update(len(chunk))
        print(f"✅ Downloaded {filename}")
    else:
        print(f"❌ Failed to download {filename}")

# Main Execution
subdirectories = get_subdirectories()
if not subdirectories:
    print("❌ No subdirectories found. Check your internet connection or PhysioNet access.")
    exit()

# Loop through each subdirectory to find files
files_to_download = []
for subdir in subdirectories:
    files_to_download.extend(get_file_list(subdir))

if not files_to_download:
    print("❌ No ECG files found to download. Exiting...")
    exit()

print(f"📄 Total files to download: {len(files_to_download)}")

# Download files
for file in files_to_download:
    download_file(file)

print(f"🎉 Dataset download complete! All files are saved in: {DEST_DIR}")

