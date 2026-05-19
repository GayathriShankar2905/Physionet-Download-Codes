pip install wfdb

import os
import requests
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

# PhysioNet Credentials
PHYSIONET_USERNAME = "your_username"
PHYSIONET_API_KEY = "your_api_key"

# Save dataset to D:\cpsc_extra
DEST_DIR = r"D:\cpsc_extra"
os.makedirs(DEST_DIR, exist_ok=True)

# Base URL for the dataset
BASE_URL = "https://physionet.org/files/challenge-2021/1.0.3/training/cpsc_2018_extra/"

# Initialize session for authentication
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

            print(f"⚠️ Attempt {attempt + 1}: Status {response.status_code}. Retrying...")

        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt + 1}: {e}")

        time.sleep(2 ** attempt)

    print(f"🚨 Failed to retrieve: {url}")
    return None

# Function to get subdirectories
def get_subdirectories():
    response = make_request(BASE_URL)

    if not response:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    subdirs = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if a["href"].endswith("/")
    ]

    return subdirs

# Function to get files inside subdirectory
def get_files(subdir):
    subdir_url = BASE_URL + subdir

    response = make_request(subdir_url)

    if not response:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    files = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if a["href"].endswith((".hea", ".mat", ".atr", ".dat"))
    ]

    return [(subdir, file) for file in files]

# Function to download files
def download_file(subdir, filename):

    url = BASE_URL + subdir + filename

    # Create corresponding subfolder
    subdir_path = os.path.join(DEST_DIR, subdir.strip("/"))
    os.makedirs(subdir_path, exist_ok=True)

    dest_path = os.path.join(subdir_path, filename)

    # Skip existing files
    if os.path.exists(dest_path):
        print(f"✅ {filename} already exists in {subdir}")
        return

    response = make_request(url)

    if response and response.status_code == 200:

        file_size = int(response.headers.get("Content-Length", 0))

        with open(dest_path, "wb") as file, tqdm(
            total=file_size,
            unit="B",
            unit_scale=True,
            desc=f"Downloading {filename}"
        ) as progress:

            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    progress.update(len(chunk))

        print(f"✅ Downloaded: {filename}")

    else:
        print(f"❌ Failed: {filename}")

# ==========================
# MAIN EXECUTION
# ==========================

print("🔍 Fetching subdirectories...")

subdirs = get_subdirectories()

if not subdirs:
    print("❌ No subdirectories found.")
    exit()

print(f"📂 Found {len(subdirs)} subdirectories.")

# Collect all files
files_to_download = []

for subdir in subdirs:
    files = get_files(subdir)
    files_to_download.extend(files)

print(f"📄 Total files to download: {len(files_to_download)}")

# Download all files
for subdir, file in files_to_download:
    download_file(subdir, file)

print(f"\n🎉 Dataset download complete!")
print(f"📁 Saved at: {DEST_DIR}")
