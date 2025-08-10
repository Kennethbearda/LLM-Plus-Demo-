from typing import Dict, Callable, Any
from functools import partial
from src.api.auth import ClientDict
import gspread
from gspread.exceptions import APIError

def get_cell_value(data: list, cell: str) -> str:
    """Get value from cell reference (e.g. 'C7') in sheet data"""
    col = ord(cell[0]) - ord('A')  # Convert 'A' to 0, 'B' to 1, etc.
    row = int(cell[1:]) - 1        # Convert '7' to 6 (0-based index)
    return data[row][col]

def get_state(clients: ClientDict) -> Dict[str, Any]:
    """Read state flags and run configuration from control panel"""
    from src.api.google.sheets import load_entire_tab
    from src.constants import OVERSEER_SHEET_ID, CELL_REF_MAP
    from src.utils.timer import get_current_time
    
    sheets = clients["sheets"]
    
    # Load entire control panel tab
    data = load_entire_tab(
        client=sheets,
        sheet_id=OVERSEER_SHEET_ID,
        sheet_tab="CONTROL_PANEL"
    )
    
    # Check if system is ready
    toggle_value = get_cell_value(data, CELL_REF_MAP["toggle_button"])
    if toggle_value != "start":
        return None
    
    # Extract values using CELL_REF_MAP
    run_mode = get_cell_value(
        data, 
        CELL_REF_MAP["run_mode"]
    )
    
    state = {
        "start_flag": toggle_value == "start",  # Set based on toggle value
        "template_file": get_cell_value(
            data, 
            CELL_REF_MAP["template_file_name"]
        ),
        
        "run_mode": run_mode,
        
        "run_duration": (
            int(get_cell_value(
                data, 
                CELL_REF_MAP["run_duration_hours"]
            ))
            if run_mode == "wait_for_uploads" 
            else None
        ),
        "timestamp": get_current_time(),
    }
    
    return state

def create_state_machine(clients: ClientDict) -> Callable[[], tuple[Callable, dict]]:
    from src.orchestrator.handlers import (
        process_uploads_handler,
        process_ledger_handler,
        wait_for_uploads_handler,
        wait_handler,
    )
    HANDLER_MAP = {
        "process_uploads": process_uploads_handler,
        "process_ledger": process_ledger_handler,
        "wait_for_uploads": wait_for_uploads_handler,
        "waiting": wait_handler,
    }

    def run_state_machine():
        from gspread.exceptions import APIError
        from src.api.auth import auth_gsheets

        try:
            state = get_state(clients)
            mode = state["run_mode"] if state else "waiting"
            handler = HANDLER_MAP.get(mode, wait_handler)
            return handler, (state or {})
        except APIError as e:
            print(f"API Error: {e}. Reauthenticating...")
            auth_gsheets(clients)
            return wait_handler, {}

    return run_state_machine