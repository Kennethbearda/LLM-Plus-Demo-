from typing import Dict, Any, List, Tuple
import heapq

def process_ledger(ledger_2d: List[List[str]]) -> List[Dict[str, str]]:
    """
    Returns a priority queue of dictionaries containing question data.
    Only includes questions where column H is not marked with 'X'.
    """
    if len(ledger_2d) < 2:
        return []
    
    headers = ledger_2d[1]  # Second row is the header
    priority_queue = []
    
    # Debug print headers
    print(f"Headers found: {headers}")
    
    for row_idx, row in enumerate(ledger_2d[2:], start=3):  # Skip header rows, start=3 for 1-based row numbers
        # Debug print row
        print(f"Processing row {row_idx}: {row}")
        
        # Pad row to match headers length
        row_padded = row + [''] * (len(headers) - len(row))
        
        # Skip if column H (index 7) is marked with 'X'
        if len(row_padded) > 7 and row_padded[7].strip().upper() == 'X':
            print(f"Skipping row {row_idx} - marked with X")
            continue
            
        # Create dictionary with required columns
        question_data = {
            'number': int(row_padded[1] if row_padded[1].strip() else '0'),  # Column B
            'operation': row_padded[2].strip(),  # Column C
            'instance': row_padded[3].strip(),   # Column D
            'present': row_padded[4].strip(),    # Column E
            'attachments': row_padded[5].strip(), # Column F
            'reload_question': row_padded[6].strip().upper() == 'X'  # Column G
        }
        
        # Debug print processed data
        print(f"Processed data for row {row_idx}: {question_data}")
        
        # Add to priority queue (using number as priority)
        heapq.heappush(priority_queue, (question_data['number'], question_data))
    
    # Extract just the dictionaries from the priority queue, maintaining order
    result = [item[1] for item in sorted(priority_queue)]
    print(f"Final processed questions: {result}")
    return result

