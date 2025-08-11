import sys
import time
import argparse
from pathlib import Path
from collections import Counter

# --- Ensure /src is on sys.path (fix) ----------------------------------------
ROOT = Path(__file__).parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# --- Real pipeline imports (safe to import; executed only in real run) -------
from src.api.auth import ClientDict  # type: ignore
from src.api.google.sheets import write_cell_value  # type: ignore
from src.orchestrator.state_machine import create_state_machine  # type: ignore

# -----------------------------------------------------------------------------


def run_loop(clients: ClientDict):
    """Original loop that polls the state machine and writes the toggle cell."""
    from src.constants import CELL_REF_MAP  # local import to keep demo light
    state_machine = create_state_machine(clients)
    sheets = clients["sheets"]

    while True:
        handler, state = state_machine()
        handler(state, clients)

        if handler.__name__ != "wait_handler":
            write_cell_value(sheets, "finished", "CONTROL_PANEL", CELL_REF_MAP["toggle_button"])

        time.sleep(0.5)


def run_real():
    """Your original main-path that uses Google clients."""
    from src.api.auth import init_clients  # local import to avoid side effects in demo
    clients = init_clients()
    run_loop(clients)


# -------------------------- DEMO MODE (no APIs) ------------------------------
def run_demo():
    """
    Runs a zero-dependency demo:
    - Simulates outputs from multiple models
    - Computes a consensus via majority vote
    - Prints results to stdout (no Google, no API keys)
    """
    model_outputs = {
        "GPT": "42",
        "Claude": "42",
        "Gemini": "42",
        "DeepSeek": "41",
    }

    consensus, _ = Counter(model_outputs.values()).most_common(1)[0]

    print("Model outputs:")
    for name, out in model_outputs.items():
        print(f" - {name}: {out}")
    print(f"\nConsensus Result: {consensus}")


# ------------------------------- Entrypoint ----------------------------------
def main():
    parser = argparse.ArgumentParser(description="LLM Plus runner")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode (no APIs needed).")
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_real()


if __name__ == "__main__":
    main()
