import os
import requests
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

# =========================
# CONFIG
# =========================

PHYSIONET_USERNAME = "your_username"
PHYSIONET_API_KEY = "your_api_key"

DEST_DIR = r"D:\mimic-iv-ecg"
os.makedirs(DEST_DIR, exist_ok=True)

BASE_URL = "https://physionet.org/files/mimic-iv-ecg/1.0/files/"

# =========================
# SESSION
# =========================

session = requests.Session()
session.auth = (PHYSIONET_USERNAME, PHYSIONET_API_KEY)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# =========================
# REQUEST FUNCTION
# =========================

def make_request(url):

    try:
        response = session.get(url, headers=HEADERS, timeout=30)

        if response.status_code == 200:
            return response

        print(f"❌ Status {response.status_code}: {url}")

    except Exception as e:
        print(f"❌ Error: {e}")

    return None

# =========================
# DOWNLOAD FUNCTION
# =========================

def download_file(url, save_path):

    if os.path.exists(save_path):
        return

    response = make_request(url)

    if response is None:
        return

    file_size = int(response.headers.get("Content-Length", 0))

    with open(save_path, "wb") as f, tqdm(
        total=file_size,
        unit="B",
        unit_scale=True,
        desc=os.path.basename(save_path)
    ) as pbar:

        for chunk in response.iter_content(chunk_size=8192):

            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

# =========================
# GET LINKS
# =========================

def get_links(url):

    response = make_request(url)

    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if a["href"] not in ["../"]
    ]

    return links

# =========================
# MAIN
# =========================

print("🔍 Starting MIMIC-IV-ECG downloader...")

top_dirs = get_links(BASE_URL)

for top_dir in top_dirs:

    if not top_dir.startswith("p"):
        continue

    print(f"\n📂 Processing {top_dir}")

    top_url = BASE_URL + top_dir

    patient_dirs = get_links(top_url)

    for patient_dir in patient_dirs:

        patient_url = top_url + patient_dir

        study_dirs = get_links(patient_url)

        for study_dir in study_dirs:

            study_url = patient_url + study_dir

            files = get_links(study_url)

            # Create save directory
            save_dir = os.path.join(
                DEST_DIR,
                top_dir.strip("/"),
                patient_dir.strip("/"),
                study_dir.strip("/")
            )

            os.makedirs(save_dir, exist_ok=True)

            for file in files:

                if file.endswith(".hea") or file.endswith(".dat"):

                    file_url = study_url + file
                    save_path = os.path.join(save_dir, file)

                    print(f"⬇️ Downloading {file}")

                    download_file(file_url, save_path)

print("\n🎉 Download complete!")
print(f"📁 Saved at: {DEST_DIR}")
