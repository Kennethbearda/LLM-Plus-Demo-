from typing import Dict, Any
from src.api.auth import ClientDict
from src.api.google.sheets import download_all_tabs
import time
from pathlib import Path

def process_uploads_handler(data: Dict[str, Any], clients: ClientDict) -> None:
    """Handle processing uploaded files"""
    from src.processes.template import print_input_from_json, find_next_row_number
    from src.processes.processor import read_input, save_final_output_to_json
    from src.processes.present import parse_present_tab
    from src.api.google.drive import (
        list_new_uploads, 
        download_fileids_to_local, 
        relocate_fileids,
        get_fileid_from_names
    )
    from src.constants import UPLOADS_FOLDER_ID, DOWNLOAD_DIR, ARCHIVE_FOLDER_ID, TEMPLATES_FOLDER_ID
    
    print(f"📤 Processing uploads with state: {data}")
    # Get list of files in uploads folder
    files = list_new_uploads(clients["drive"], UPLOADS_FOLDER_ID)

    # Extract file IDs
    file_ids = list(files.keys())  # Extract keys (file IDs) from the dict

    print(f"File IDs: {file_ids}")
    
    # Download files to local directory
    downloaded_paths = download_fileids_to_local(
        drive=clients["drive"],
        file_ids=file_ids,
        download_dir=Path(DOWNLOAD_DIR),
        source_folder_id=UPLOADS_FOLDER_ID
    )
    
    # Move files to archive
    success = relocate_fileids(
        drive=clients["drive"],
        file_ids=file_ids,
        destination_folder_id=ARCHIVE_FOLDER_ID,
        source_folder_id=UPLOADS_FOLDER_ID
    )
    
    if not success:
        print("Warning: Failed to move some files to archive")
    
    print(f"Downloaded {len(downloaded_paths)} files: {downloaded_paths}")
    
    # Get template file ID
    fileid_map = get_fileid_from_names(clients["drive"], [data["template_file"]], TEMPLATES_FOLDER_ID)
    template_fileid = fileid_map[data["template_file"]]
    
    # Get all tabs from template
    all_tabs = download_all_tabs(clients["sheets"], template_fileid)
    
    # Get CV present tab
    cv_present = parse_present_tab(all_tabs.get("CV_PRESENT", []))
    
    # Process the files
    results = read_input(clients, cv_present, downloaded_paths)

    # Save results to JSON
    output_path = Path(DOWNLOAD_DIR) / "model_output.json"
    save_final_output_to_json(results, str(output_path))
    print(f"💾 Saved model output to: {output_path}")

    # Get next row number and print to sheets
    next_row = find_next_row_number(all_tabs.get("LEDGER", []))
    print(f"📊 Next row number in sheet: {next_row}")
    print_input_from_json(clients["sheets"], str(output_path), next_row, template_fileid)

    # Call process_ledger_handler
    process_ledger_handler(data, clients)
    
    return

def process_ledger_handler(data: Dict[str, Any], clients: ClientDict) -> None:
    """
    Handles the processing of ledger data, including downloading tabs, evaluating questions,
    and writing results back to the sheet.
    
    Args:
        data: Dictionary containing the request data
        clients: Dictionary of client instances
    """
    from src.processes.processor import evaluate_row
    from src.utils.json import (
        serialize_ledger_into_json, 
        update_question_inside_json, 
        read_json_file, 
    )
    from src.processes.template import print_output_from_json
    from src.processes.present import parse_present_tab
    from src.utils.timer import convert_timestamp_to_safe_format
    from pathlib import Path
    from src.api.google.drive import get_fileid_from_names
    from src.constants import TEMPLATES_FOLDER_ID
    
    print(f"📝 Processing ledger with state: {data}")
    
    # Get template file ID
    fileid_map = get_fileid_from_names(clients["drive"], [data["template_file"]], TEMPLATES_FOLDER_ID)
    template_fileid = fileid_map[data["template_file"]]
    
    # Download all tabs from the template file
    all_tabs = download_all_tabs(clients["sheets"], template_fileid)
    
    # Extract the LEDGER tab and save to JSON
    timestamp_str = data["timestamp"]
    serialize_ledger_into_json(all_tabs.get("LEDGER", []), convert_timestamp_to_safe_format(timestamp_str))
    
    # Convert timestamp to filesystem-safe format
    safe_timestamp = convert_timestamp_to_safe_format(timestamp_str)
    
    # Read questions from JSON file
    json_file = Path("outputs") / f"{safe_timestamp}.json"
    questions = read_json_file(json_file)
    print(f"Questions from JSON: {questions}")
    
    # Initialize presents dictionary to cache loaded presents
    presents = {}
    
    # Process each question in priority order
    for question in questions:
        present_name = question['present']

        if question['resolved']:
            continue

        if question['reload_question']:
            print(f"Reloading question {question['question_number']}")
            # TODO: Reload the question
            continue
        
        # Load present if not already loaded
        if present_name not in presents:
            present_tab = all_tabs.get(present_name, [])
            if not present_tab:
                print(f"Warning: Present tab '{present_name}' not found, using 'TEST_PRESENT'.")
                present_name = "TEST_PRESENT"
                present_tab = all_tabs.get(present_name, [])
                if not present_tab:
                    print(f"Warning: Present tab '{present_name}' not found, using 'TEST_PRESENT'.")
                    continue
            presents[present_name] = parse_present_tab(present_tab)
        
        # Evaluate the present with the question
        eval_results = evaluate_row(
            presents[present_name],
            question['question'],
            clients,
        )
        print(f"[DEBUG] Results for question {question['question_number']}: {eval_results}")
        
        # Update question in JSON with results
        question['model_outputs'] = eval_results
        question['resolved'] = True
        update_question_inside_json(question, convert_timestamp_to_safe_format(data["timestamp"]))
    
    # Write all results back to sheets
    print_output_from_json(clients["sheets"], str(json_file), template_fileid)
    
    return

def wait_for_uploads_handler(data: Dict[str, Any], clients: ClientDict) -> None:
    """Handle waiting for new uploads"""
    print(f"⏳ Waiting for uploads with state: {data}")
    if watchtower(clients["drive"]):
        return
    return

def wait_handler(data: Dict[str, Any], clients: ClientDict) -> None:
    """Handle waiting state"""
    print(f"⏳ Waiting for system to be ready...")
    time.sleep(10)
    return