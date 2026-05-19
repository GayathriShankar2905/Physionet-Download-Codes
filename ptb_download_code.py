pip install wfdb

import os
import requests
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

# ============================================================
# PHYSIONET CREDENTIALS
# ============================================================
PHYSIONET_USERNAME = "your_username"
PHYSIONET_API_KEY = "your_api_key"

# ============================================================
# SAVE LOCATION -> D:\ptb
# ============================================================
DEST_DIR = r"D:\ptb"
os.makedirs(DEST_DIR, exist_ok=True)

# ============================================================
# PTB DATASET URL
# ============================================================
BASE_URL = "https://physionet.org/files/challenge-2021/1.0.3/training/ptb/"

# ============================================================
# SETTINGS
# ============================================================
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 30
MAX_RETRIES = 5

# ============================================================
# AUTHENTICATED SESSION
# ============================================================
session = requests.Session()
session.auth = (PHYSIONET_USERNAME, PHYSIONET_API_KEY)

# ============================================================
# REQUEST FUNCTION
# ============================================================
def make_request(url):

    for attempt in range(MAX_RETRIES):

        try:
            response = session.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                return response

            print(f"⚠️ Attempt {attempt + 1}: Status {response.status_code}")

        except requests.exceptions.RequestException as e:

            print(f"❌ Attempt {attempt + 1}: {e}")

        time.sleep(2 ** attempt)

    print(f"🚨 Failed to retrieve: {url}")

    return None

# ============================================================
# GET ALL SUBDIRECTORIES
# ============================================================
def get_subdirectories():

    response = make_request(BASE_URL)

    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    subdirs = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if href.endswith("/") and href != "../":
            subdirs.append(href)

    return subdirs

# ============================================================
# GET FILES FROM EACH SUBDIRECTORY
# ============================================================
def get_files_from_subdir(subdir):

    subdir_url = BASE_URL + subdir

    response = make_request(subdir_url)

    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    files = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if href.endswith(".hea") or href.endswith(".mat") or href.endswith(".csv"):
            files.append((subdir, href))

    return files

# ============================================================
# DOWNLOAD FILE
# ============================================================
def download_file(subdir, filename):

    file_url = BASE_URL + subdir + filename

    # Create subfolder
    save_folder = os.path.join(DEST_DIR, subdir.rstrip("/"))
    os.makedirs(save_folder, exist_ok=True)

    save_path = os.path.join(save_folder, filename)

    # Skip if exists
    if os.path.exists(save_path):
        print(f"✅ Already exists: {filename}")
        return

    response = make_request(file_url)

    if response is None:
        print(f"❌ Failed: {filename}")
        return

    file_size = int(response.headers.get("Content-Length", 0))

    with open(save_path, "wb") as f, tqdm(
        total=file_size,
        unit="B",
        unit_scale=True,
        desc=f"Downloading {filename}"
    ) as progress:

        for chunk in response.iter_content(chunk_size=1024):

            if chunk:
                f.write(chunk)
                progress.update(len(chunk))

    print(f"✅ Downloaded: {filename}")

# ============================================================
# MAIN
# ============================================================
print("🔍 Finding PTB dataset folders...")

subdirs = get_subdirectories()

if len(subdirs) == 0:
    print("❌ No subdirectories found.")
    exit()

print(f"📂 Found {len(subdirs)} folders")

# ============================================================
# COLLECT ALL FILES
# ============================================================
all_files = []

for subdir in subdirs:

    files = get_files_from_subdir(subdir)

    all_files.extend(files)

print(f"📄 Total files found: {len(all_files)}")

# ============================================================
# DOWNLOAD EVERYTHING
# ============================================================
for subdir, filename in all_files:

    download_file(subdir, filename)

# ============================================================
# FINISHED
# ============================================================
print("\n🎉 PTB dataset download complete!")
print(f"📁 Dataset saved in: {DEST_DIR}")
