# File: processes/template.py

from typing import List, Dict
import gspread

def print_output(
    sheets_client: gspread.Client, 
    eval_steps: List[Dict[str, str]], 
    row_number: int, 
    sheet_id: str, 
    tab_name: str = "LEDGER"
) -> None:
    """
    Batch writes evaluation outputs to a row in the 'LEDGER' sheet.
    Column mapping:
    - H: X flag
    - I: Claude (Step 1)
    - J: Deepseek (Step 1)
    - K: Gemini (Step 1)
    - L: GPT (Step 1)
    - M: Claude (Step 2)
    - N: Deepseek (Step 2)
    - O: Gemini (Step 2)
    - P: GPT (Step 2)
    And so on for subsequent steps...
    """
    try:
        # Get the worksheet
        worksheet = sheets_client.open_by_key(sheet_id).worksheet(tab_name)
        
        # Get existing row data (offset by 2 to account for header row)
        existing_row = worksheet.row_values(row_number + 2)
        
        # Ensure row is at least 8 columns long (A through H)
        while len(existing_row) < 8:
            existing_row.append("")
        
        # Set X flag in column H (index 7)
        existing_row[7] = "X"
        
        # Map each step's outputs to their respective columns
        for step_index, step in enumerate(eval_steps):
            # Calculate base column index for this step
            # Step 1 starts at I (index 8), Step 2 at M (index 12), etc.
            base_col = 8 + (step_index * 4)
            
            # Extend row if needed
            while len(existing_row) <= base_col + 3:
                existing_row.append("")
                
            # Map each model's output to its column
            for model, output in step.items():
                if model == "CLAUDE":
                    existing_row[base_col] = output
                elif model == "DEEPSEEK":
                    existing_row[base_col + 1] = output
                elif model == "GEMINI":
                    existing_row[base_col + 2] = output
                elif model == "GPT":
                    existing_row[base_col + 3] = output

        # Calculate the last column letter
        last_col = chr(ord('A') + len(existing_row) - 1)
        
        # Update the row (offset by 2 to account for header row)
        worksheet.update(f"A{row_number+2}:{last_col}{row_number+2}", [existing_row])

    except Exception as e:
        raise RuntimeError(f"[print_output] Failed to write to {tab_name} at row {row_number}: {str(e)}")

def print_input(
    sheets_client: gspread.Client,
    results: List[Dict[str, str]],
    start_row: int,
    sheet_id: str,
    tab_name: str = "LEDGER",
) -> None:
    import traceback
    import json

    try:
        print("🔍 [print_input] Starting write process...")
        print(f"📋 Sheet ID: {sheet_id}")
        print(f"📄 Target tab: {tab_name}")
        print(f"📐 Start row: {start_row}")

        sheet = sheets_client.open_by_key(sheet_id)
        print("✅ Sheet opened successfully")

        worksheet = sheet.worksheet(tab_name)
        print("✅ Worksheet (tab) accessed successfully")

        # Get the final result which should contain the JSON
        final_result = results[-1]
        if len(final_result) != 1:
            raise ValueError(f"Expected exactly one model output, got {len(final_result)}")
        
        # Get the JSON string and parse it
        json_str = next(iter(final_result.values()))
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1]
        if json_str.endswith("```"):
            json_str = json_str.rsplit("```", 1)[0]
        json_str = json_str.strip()
        
        questions = json.loads(json_str)
        print(f"📝 Number of questions: {len(questions)}")

        for i, (q_num, question) in enumerate(questions.items()):
            row_number = start_row + i
            op = question.get("operation", "")
            inst = question.get("instance", "")

            print(f"➡️  Writing to row {row_number}: [Row#={row_number}, Question={q_num}, OPERATION={op}, INSTANCE={inst}]")

            worksheet.update(f"B{row_number}:D{row_number}", [[
                str(row_number),  # ✅ Write actual row number
                op,
                inst
            ]])

        print("✅ [print_input] All questions written successfully.")

    except Exception as e:
        print("❌ [print_input] Exception occurred:")
        traceback.print_exc()
        raise RuntimeError(f"[print_input] Failed to write to rows starting at {start_row}: {str(e)}")

def find_next_row_number(ledger_2d: List[List[str]]) -> int:
    """
    Find the next row number by checking column B (index 1) in the 2D list.
    Returns the next number after the highest number found.
    If no numbers found, returns 1.
    """
    # Skip header rows (first 2 rows)
    numbers = []
    for row in ledger_2d[2:]:
        if len(row) > 1:  # Make sure row has at least 2 columns
            try:
                if row[1].strip():  # Only try to convert non-empty values
                    numbers.append(int(row[1]))
            except ValueError:
                continue
    
    # If no numbers found, start with 1
    if not numbers:
        return 1
        
    # Return next number after highest
    return max(numbers) + 1

def print_output_from_json(
    sheets_client: gspread.Client,
    json_file_path: str,
    sheet_id: str,
    tab_name: str = "LEDGER"
) -> None:
    """Write model outputs from JSON file back to Google Sheets (simple version)."""
    import json

    print("🔍 [print_output_from_json] Starting write process...")
    print(f"📋 Sheet ID: {sheet_id}")
    print(f"📄 Target tab: {tab_name}")
    print(f"📁 Reading from: {json_file_path}")

    with open(json_file_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    print(f"📝 Number of questions: {len(questions)}")

    sheet = sheets_client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(tab_name)
    print("✅ Sheet accessed successfully")

    def has_content_in_step(step):
        """Check if a step has any non-empty model outputs."""
        return any(
            step.get(model, "").strip() != "" 
            for model in ["CLAUDE", "DEEPSEEK", "GEMINI", "GPT"]
        )

    def get_column_letter(col_number):
        """Convert column number to Excel column letter (1=A, 2=B, 27=AA, etc.)."""
        result = ""
        while col_number > 0:
            col_number -= 1
            result = chr(col_number % 26 + ord('A')) + result
            col_number //= 26
        return result

    # Process each question individually
    for question in questions:
        row_number = question['question_number']
        print(f"\n--- Processing Question {row_number} ---")
        
        # Start with basic columns
        row_data = []
        row_data.append(str(question['question_number']))  # B (column 2)
        row_data.append(question['question'])              # C (column 3)
        row_data.append(question['present'])               # D (column 4)
        row_data.append("X" if question.get('reload_question') else "")  # E (column 5)
        row_data.append("X" if question.get('resolved') else "")         # F (column 6)
        
        print(f"  Basic columns: {len(row_data)}")
        
        # Add model outputs starting at column G (index 6)
        # Pattern: G=CLAUDE, H=DEEPSEEK, I=GEMINI, J=GPT, K=CLAUDE, L=DEEPSEEK, etc.
        model_outputs = question.get('model_outputs', [])
        content_steps = 0
        
        for step_index, step in enumerate(model_outputs):
            if has_content_in_step(step):
                # Always add in the specific order: CLAUDE, DEEPSEEK, GEMINI, GPT
                claude_output = step.get("CLAUDE", "").strip()
                deepseek_output = step.get("DEEPSEEK", "").strip() 
                gemini_output = step.get("GEMINI", "").strip()
                gpt_output = step.get("GPT", "").strip()
                
                row_data.extend([claude_output, deepseek_output, gemini_output, gpt_output])
                content_steps += 1
                
                # Show which columns this step occupies
                current_step_start = 7 + (content_steps - 1) * 4  # G=7, K=11, O=15, etc.
                current_step_cols = [get_column_letter(current_step_start + i) for i in range(4)]
                print(f"  Step {step_index} -> Columns {current_step_cols[0]}-{current_step_cols[3]} (CLAUDE,DEEPSEEK,GEMINI,GPT)")
        
        print(f"  Content steps: {content_steps}")
        print(f"  Final row length: {len(row_data)}")
        
        # Verify the column mapping
        if len(row_data) > 5:
            model_start_col = get_column_letter(7)  # G
            model_end_col = get_column_letter(6 + (content_steps * 4))  # Last model column
            print(f"  Model outputs span: {model_start_col} to {model_end_col}")
        
        # Calculate range
        start_col_num = 2  # B = column 2
        end_col_num = start_col_num + len(row_data) - 1
        
        start_col = get_column_letter(start_col_num)  # B
        end_col = get_column_letter(end_col_num)
        
        target_row = row_number + 2  # Assuming header rows
        range_str = f'{start_col}{target_row}:{end_col}{target_row}'
        
        print(f"  Writing to range: {range_str}")
        print(f"  Data preview: {[str(x)[:20] + '...' if len(str(x)) > 20 else str(x) for x in row_data[:3]]}...")
        
        # Write the row
        worksheet.update(range_str, [row_data])
        print(f"  ✅ Successfully wrote {len(row_data)} columns")

    print("\n✅ [print_output_from_json] All data written successfully.")