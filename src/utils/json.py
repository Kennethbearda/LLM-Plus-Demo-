from typing import List, Dict
import json
from pathlib import Path

def serialize_ledger_into_json(ledger: List[List[str]], timestamp: str) -> None:
    """
    Transforms ledger data into a structured JSON format and saves to a timestamped file.

    Args:
        ledger: 2D list of strings representing the ledger data
        timestamp: Timestamp string in format "YYYYMMDD_HHMMSS"
    """
    if len(ledger) < 2:
        print("❌ Not enough rows in ledger to process.")
        return

    headers = ledger[1]
    models = ["CLAUDE", "DEEPSEEK", "GEMINI", "GPT"]
    questions = []

    def clean(cell: str) -> str:
        return (cell or "").replace('\xa0', '').strip().upper()

    for row in ledger[2:]:
        question_number = int(row[1]) if len(row) > 1 and row[1].strip().isdigit() else 0

        question = {
            "question_number": question_number,
            "question": row[2].strip() if len(row) > 2 else "",
            "present": row[3].strip() if len(row) > 3 else "",
            "reload_question": clean(row[4]) == "X" if len(row) > 4 else False,
            "resolved": clean(row[5]) == "X" if len(row) > 5 else False,
            "model_outputs": []
        }

        # From column G (index 6) onward: 4 models per step
        for step in range((len(headers) - 6) // 4):
            base = 6 + step * 4
            step_outputs = {
                model: row[base + i].strip() if base + i < len(row) else ""
                for i, model in enumerate(models)
            }
            question["model_outputs"].append(step_outputs)

        questions.append(question)

    # Save JSON
    output_path = Path("outputs") / f"{timestamp}.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON saved to: {output_path}")


def update_question_inside_json(question: Dict, timestamp: str) -> None:
    """
    Updates or inserts a question in the JSON file with the given timestamp.
    
    Args:
        timestamp: Timestamp string in format "%m/%d/%Y %H:%M:%S" (e.g., "03/15/2024 14:30:22")
        question: Dictionary containing the question data to update/insert
    """
    # Convert timestamp to filesystem-safe format (YYYYMMDD_HHMMSS)

    json_file = Path("outputs") / f"{timestamp}.json"
    
    # ✅ Use shared utility to read file
    questions = read_json_file(json_file) if json_file.exists() else []
    
    # Find if question already exists
    question_number = question["question_number"]
    for i, q in enumerate(questions):
        if q["question_number"] == question_number:
            # Update existing question
            questions[i] = question
            break
    else:
        # Insert new question
        questions.append(question)
    
    # Sort questions by question number
    questions.sort(key=lambda x: x["question_number"])
    
    # Write back to file
    with open(json_file, 'w') as f:
        json.dump(questions, f, indent=2)
    
    print(f"✅ Updated question {question_number} in {json_file}")

def read_json_file(file_path: Path) -> List[Dict]:
    """
    Reads and returns the contents of a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        List of question dictionaries
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)