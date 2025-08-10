from pathlib import Path
from typing import List, Tuple, Dict
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload
from constants import UPLOADS_FOLDER_ID, ARCHIVE_FOLDER_ID, DOWNLOAD_DIR

def list_new_uploads(drive: Resource) -> list[dict]:
    """
    Queries Drive for all non-trashed, non-folder files in the UPLOADS_FOLDER_ID folder.

    Args:
        drive: an authenticated googleapiclient.discovery.Resource for Drive v3.

    Returns:
        A list of file-metadata dicts, each containing keys: "id", "name", and "mimeType".
        If the folder is empty or only contains folders, returns an empty list.
    """
    resp = drive.files().list(
        q=(
            f"'{UPLOADS_FOLDER_ID}' in parents "
            "and trashed=false "
            "and mimeType!='application/vnd.google-apps.folder'"
        ),
        fields="files(id,name,mimeType)"
    ).execute()
    return resp.get("files", [])

def download_file(drive: Resource, file_id: str, filename: str) -> Path:
    """
    Streams the binary content of a Drive file down to your local DOWNLOAD_DIR.

    Args:
        drive: an authenticated googleapiclient.discovery.Resource for Drive v3.
        file_id: the ID of the file to download.
        filename: the desired filename under DOWNLOAD_DIR.

    Returns:
        The full local path where the file was saved (Path object).
    """
    import re
    
    download_dir = Path(DOWNLOAD_DIR)
    download_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = re.sub(r'[<>:"/\\|?*\u202f]', '_', filename)
    local_path = download_dir / safe_filename
    print(f"[DOWNLOAD] Preparing to download to: {local_path}")

    request = drive.files().get_media(fileId=file_id)

    with local_path.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        print(f"[DOWNLOAD] Starting download for file ID: {file_id}")
        while not done:
            try:
                status, done = downloader.next_chunk()
                if status:
                    print(f"[DOWNLOAD] Progress: {int(status.progress() * 100)}%")
            except Exception as e:
                print(f"[ERROR] Failed during download chunk for {file_id}: {e}")
                raise

    print(f"[DOWNLOAD] ✅ File downloaded and saved to: {local_path}")
    return local_path

def download_files(drive: Resource) -> Tuple[List[Path], List[str]]:
    """
    Downloads all non-folder files from UPLOADS_FOLDER_ID on Google Drive.

    Returns:
        - local_paths: List of sanitized Path objects where each file was saved locally
        - original_names: List of the original Google Drive filenames
          (used for accurate lookup in move_to_archive)
    """
    print("[BATCH DOWNLOAD] Checking for new uploads...")
    files = list_new_uploads(drive)
    print(f"[BATCH DOWNLOAD] Found {len(files)} file(s) to download.")

    local_paths: List[Path] = []
    original_names: List[str] = []

    for idx, file_meta in enumerate(files):
        file_id = file_meta["id"]
        original_name = file_meta["name"]
        print(f"[{idx+1}/{len(files)}] Downloading: {original_name} (ID: {file_id})")

        try:
            path = download_file(drive, file_id, original_name)
            local_paths.append(path)
            original_names.append(original_name)
        except Exception as e:
            print(f"[ERROR] Failed to download '{original_name}' (ID: {file_id}): {e}")

    print(f"[BATCH DOWNLOAD] ✅ Completed. {len(local_paths)} file(s) successfully downloaded.")
    return local_paths, original_names

def move_to_archive(drive: Resource, filenames: List[str]) -> None:
    """
    Moves files from UPLOADS_FOLDER_ID to ARCHIVE_FOLDER_ID on Google Drive
    by exact name match (no longer relying on Path.name).

    Args:
        drive: Authenticated Google Drive API resource.
        filenames: Original filenames as they appear on Drive.
    """
    print(f"📦 Archiving {len(filenames)} file(s)...")

    archived = 0
    failed = 0

    for filename in filenames:
        print(f"🔍 Searching for: {filename}")

        try:
            query = (
                f"name = '{filename}' and "
                f"'{UPLOADS_FOLDER_ID}' in parents and "
                "trashed = false"
            )
            result = drive.files().list(q=query, fields="files(id)").execute()
            files = result.get("files", [])

            if not files:
                print(f"⚠️ File not found in uploads folder: {filename}")
                failed += 1
                continue

            file_id = files[0]["id"]

            drive.files().update(
                fileId=file_id,
                addParents=ARCHIVE_FOLDER_ID,
                removeParents=UPLOADS_FOLDER_ID,
                fields="id, parents"
            ).execute()

            print(f"✅ Archived: {filename}")
            archived += 1

        except Exception as e:
            print(f"❌ Failed to archive {filename}: {e}")
            failed += 1

    print(f"📊 Archive complete: {archived} moved, {failed} failed.") 