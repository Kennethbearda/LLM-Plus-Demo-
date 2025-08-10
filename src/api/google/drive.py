from pathlib import Path
from typing import List, Tuple, Dict
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload
import re


def list_new_uploads(
    drive: Resource,
    folder_id: str
) -> Dict[str, Tuple[str, str]]:
    """
    Lists all files in a specified folder.
    
    Args:
        drive: Authenticated Google Drive API resource
        folder_id: ID of the folder to search in
    
    Returns:
        Dictionary mapping file_id to tuple of (name, mime_type)
    """
    try:
        query = (
            f"'{folder_id}' in parents "
            "and trashed=false "
            "and mimeType!='application/vnd.google-apps.folder'"
        )
        
        response = drive.files().list(
            q=query,
            fields="files(id,name,mimeType)"
        ).execute()
        
        files = response.get("files", [])
        result = {
            file["id"]: (file["name"], file["mimeType"]) 
            for file in files
        }
        
        return result
        
    except Exception:
        return {}


def identify_illegal_file_formats(
    files: Dict[str, Tuple[str, str]]
) -> Dict[str, Tuple[str, str]]:
    """
    Identifies files with unsupported formats.
    
    Args:
        files: Dictionary mapping file_id to tuple of (name, mime_type)
    
    Returns:
        Tuple containing:
        - Success boolean
        - Dictionary of invalid files (same format as input) or None if no invalid files
    """
    # List of supported MIME types
    SUPPORTED_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp'
    }
    
    invalid_files = {
        file_id: (name, mime_type)
        for file_id, (name, mime_type) in files.items()
        if mime_type not in SUPPORTED_TYPES
    }
    
    return invalid_files if invalid_files else None


def get_fileid_from_names(
    drive: Resource,
    filenames: List[str],
    folder_id: str
) -> Dict[str, str]:
    """
    Gets file IDs for a list of filenames in a specific folder.
    Throws error if duplicate filenames are found.
    
    Args:
        drive: Authenticated Google Drive API resource
        filenames: List of filenames to look up
        folder_id: ID of the folder to search in
    
    Returns:
        Tuple containing:
        - Dictionary mapping filename to file_id
        - Success boolean
    """
    try:
        # Build query for all files at once
        name_conditions = " or ".join(f"name = '{name}'" for name in filenames)
        query = f"({name_conditions}) and '{folder_id}' in parents and trashed = false"
        
        result = drive.files().list(
            q=query,
            fields="files(id,name)"
        ).execute()
        
        files = result.get("files", [])
        
        # Check for duplicates
        name_count = {}
        for file in files:
            name_count[file["name"]] = name_count.get(file["name"], 0) + 1
            
        duplicates = [name for name, count in name_count.items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate filenames found: {duplicates}")
            
        # Create mapping
        file_map = {file["name"]: file["id"] for file in files}
        
        # Verify all requested files were found
        missing = set(filenames) - set(file_map.keys())
        if missing:
            raise FileNotFoundError(f"Files not found: {missing}")
            
        return file_map
        
    except Exception:
        return {}

def download_fileids_to_local(
    drive: Resource,
    file_ids: List[str],
    download_dir: Path,
    source_folder_id: str
) -> List[str]:
    """
    Downloads files by their IDs to a local directory.
    
    Args:
        drive: Authenticated Google Drive API resource
        file_ids: List of file IDs to download
        download_dir: Path to download directory
        source_folder_id: ID of the folder containing the files
    
    Returns:
        Tuple containing:
        - List of downloaded file paths (as strings)
        - Success boolean
    """
    try:
        # Ensure download directory exists
        download_dir.mkdir(parents=True, exist_ok=True)
        downloaded_paths = []
        
        # Verify all files are in the source folder
        for file_id in file_ids:
            file = drive.files().get(
                fileId=file_id,
                fields="name,parents"
            ).execute()
            
            if source_folder_id not in file.get("parents", []):
                raise ValueError(f"File {file_id} not found in source folder")
            
            # Sanitize filename
            safe_name = re.sub(r'[<>:"/\\|?*\u202f]', '_', file["name"])
            local_path = download_dir / safe_name
            
            # Download file
            request = drive.files().get_media(fileId=file_id)
            with local_path.open("wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                    
            downloaded_paths.append(str(local_path))
            
        return downloaded_paths
        
    except Exception:
        return []


def relocate_fileids(
    drive: Resource,
    file_ids: List[str],
    destination_folder_id: str,
    source_folder_id: str
) -> bool:
    """
    Moves files from source folder to destination folder.
    
    Args:
        drive: Authenticated Google Drive API resource
        file_ids: List of file IDs to move
        destination_folder_id: ID of the destination folder
        source_folder_id: ID of the source folder
    
    Returns:
        Boolean indicating success
    """
    try:
        for file_id in file_ids:
            # Verify file is in source folder
            file = drive.files().get(
                fileId=file_id,
                fields="parents"
            ).execute()
            
            if source_folder_id not in file.get("parents", []):
                raise ValueError(f"File {file_id} not found in source folder")
            
            # Move file
            drive.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=source_folder_id,
                fields="id, parents"
            ).execute()
            
        return True
        
    except Exception:
        return False