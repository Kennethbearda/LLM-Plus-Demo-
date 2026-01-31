import sys
import time
import argparse
from pathlib import Path
from collections import Counter
from typing import Any, Dict

# -------------------- Path setup (keep for now) --------------------
ROOT = Path(__file__).parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# -------------------- Safe type alias (no side effects) --------------------
ClientDict = Dict[str, Any]

# -------------------- REAL MODE LOOP --------------------
def run_loop(clients: ClientDict):
    """
    Original loop that polls the state machine and writes the toggle cell.
    All heavy imports are local to avoid side effects in demo mode.
    """
    from src.constants import CELL_REF_MAP
    from src.orchestrator.state_machine import create_state_machine
    from src.api.google.sheets import write_cell_value

    state_machine = create_state_machine(clients)
    sheets = clients["sheets"]

    while True:
        handler, state = state_machine()
        handler(state, clients)

        if handler.__name__ != "wait_handler":
            write_cell_value(
                sheets,
                "finished",
                "CONTROL_PANEL",
                CELL_REF_MAP["toggle_button"],
            )

        time.sleep(0.5)

# -------------------- REAL MODE ENTRY --------------------
def run_real():
    """
    Real execution path.
    Requires Google/OpenAI credentials and dependencies.
    """
    from src.api.auth import init_clients

    clients = init_clients()
    run_loop(clients)

# -------------------- DEMO MODE (NO APIs) --------------------
def run_demo():
    """
    Zero-dependency demo:
    - Simulates multi-model outputs
    - Computes consensus via majority vote
    - Prints results to stdout
    """

    model_outputs = {
        "GPT": "42",
        "Claude": "42",
        "Gemini": "42",
        "DeepSeek": "41",
    }

    consensus, _ = Counter(model_outputs.values()).most_common(1)[0]

    print("\nLLM Plus — DEMO MODE\n")
    print("Simulated model outputs:")
    for name, output in model_outputs.items():
        print(f"  • {name}: {output}")

    print(f"\nConsensus Result: {consensus}\n")

# -------------------- CLI ENTRYPOINT --------------------
def main():
    parser = argparse.ArgumentParser(description="LLM Plus runner")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo mode (no APIs or credentials required)",
    )
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_real()

if __name__ == "__main__":
    main()
