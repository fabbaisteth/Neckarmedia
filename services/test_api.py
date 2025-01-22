import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_DRIVE_API")
FOLDER_ID = "1af9TUTNrBSkaoHZrSyqYWSTYqk0UiER3"

def list_folder_files(folder_id, api_key=API_KEY):
    """
    Lists files in a publicly shared Google Drive folder using an API key.
    Returns a list of dicts with "id", "name", "mimeType".
    """
    base_url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": f"'{folder_id}' in parents and trashed=false",
        "key": api_key,
        "fields": "files(id, name, mimeType)"
    }
    r = requests.get(base_url, params=params)
    data = r.json()

    if "files" not in data:
        print("Error or no files found:", data)
        return []
    else:
        return data["files"]
    
def download_file(file_id, local_path, api_key=API_KEY):
    """
    Downloads a publicly shared file from Google Drive using an API key.
    """
    download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={api_key}"
    r = requests.get(download_url)
    if r.status_code == 200:
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Saved {file_id}")
    else:
        print(f"Error {r.status_code} downloading {file_id}: {r.text}")

def download_and_categorize_files():
    files = list_folder_files(FOLDER_ID, api_key=API_KEY)
    for f in files:
        file_id = f["id"]
        file_name = f["name"]
        mime_type = f["mimeType"]

        # Decide which subfolder to save to based on MIME type
        if mime_type == "application/pdf":
            # PDF => save in "pdfs/" folder
            local_path = os.path.join("pdfs", file_name)
            download_file(file_id, local_path)
        
        elif mime_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]:
            # Word => save in "docs/" folder
            local_path = os.path.join("docs", file_name)
            download_file(file_id, local_path)

        else:
            # Everything else => save in "misc/" folder
            # (If it's a Google Doc, you'd need OAuth to export text, so this
            #   will just download the "shortcut" object or might fail. 
            #   But at least it won't crash.)
            print(f"Unknown or unsupported MIME type '{mime_type}' for file '{file_name}'.")
            local_path = os.path.join("misc", file_name)
            download_file(file_id, local_path)

# Run the download
download_and_categorize_files()

