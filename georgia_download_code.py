pip install wfdb

import os
import requests
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

# ============================================================
# SAVE PATH -> D:\georgia
# ============================================================
DEST_DIR = r"D:\georgia"
os.makedirs(DEST_DIR, exist_ok=True)

# ============================================================
# PHYSIONET LOGIN
# ============================================================
PHYSIONET_USERNAME = "your_username"
PHYSIONET_API_KEY = "your_api_key"

# ============================================================
# GEORGIA DATASET URL
# ============================================================
BASE_URL = "https://physionet.org/files/challenge-2021/1.0.3/training/georgia/"

# ============================================================
# SESSION SETUP
# ============================================================
session = requests.Session()
session.auth = (PHYSIONET_USERNAME, PHYSIONET_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 30
MAX_RETRIES = 5

# ============================================================
# REQUEST FUNCTION
# ============================================================
def make_request(url):
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, headers=HEADERS, timeout=TIMEOUT)

            if response.status_code == 200:
                return response

            print(f"⚠️ Attempt {attempt+1}: Status {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt+1}: {e}")

        time.sleep(2 ** attempt)

    print(f"🚨 Failed to access: {url}")
    return None

# ============================================================
# GET SUBDIRECTORIES
# ============================================================
def get_subdirectories():

    response = make_request(BASE_URL)

    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    subdirs = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if href.endswith("/") and href not in ["../"]:
            subdirs.append(href)

    return subdirs

# ============================================================
# GET FILES FROM SUBDIRECTORY
# ============================================================
def get_file_list(subdir):

    subdir_url = BASE_URL + subdir

    response = make_request(subdir_url)

    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    files = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if href.endswith(".hea") or href.endswith(".mat"):
            files.append((subdir, href))

    return files

# ============================================================
# DOWNLOAD FILE
# ============================================================
def download_file(subdir, filename):

    url = BASE_URL + subdir + filename

    save_folder = os.path.join(DEST_DIR, subdir.rstrip("/"))
    os.makedirs(save_folder, exist_ok=True)

    save_path = os.path.join(save_folder, filename)

    # Skip existing file
    if os.path.exists(save_path):
        print(f"✅ Already exists: {filename}")
        return

    response = make_request(url)

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
print("🔍 Finding Georgia dataset folders...")

subdirs = get_subdirectories()

if len(subdirs) == 0:
    print("❌ No subdirectories found.")
    exit()

print(f"📂 Found {len(subdirs)} folders")

all_files = []

for subdir in subdirs:

    files = get_file_list(subdir)

    all_files.extend(files)

print(f"📄 Total files found: {len(all_files)}")

# ============================================================
# DOWNLOAD ALL FILES
# ============================================================
for subdir, filename in all_files:
    download_file(subdir, filename)

print("\n🎉 Georgia dataset download complete!")
print(f"📁 Saved to: {DEST_DIR}")
