import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from src.api.auth import ClientDict
from src.api.google.sheets import write_cell_value
from src.orchestrator.state_machine import create_state_machine

import time

def run_loop(clients: ClientDict):
    from src.constants import CELL_REF_MAP
    state_machine = create_state_machine(clients)
    sheets = clients["sheets"]

    while True:
        handler, state = state_machine()
        handler(state, clients)

        if handler.__name__ != "wait_handler":
            write_cell_value(sheets, "finished", "CONTROL_PANEL", CELL_REF_MAP["toggle_button"])

        time.sleep(0.5)


def main():
    from src.api.auth import init_clients
    
    # Initialize clients
    clients = init_clients()
    
    # Run the main loop
    run_loop(clients)


if __name__ == "__main__":
    main()