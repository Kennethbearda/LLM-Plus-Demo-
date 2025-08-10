from typing import List, Dict

def parse_present_tab(tab_2d: List[List[str]]) -> List[Dict[str, str]]:
    """
    Given a 2D list (list of lists of strings) representing a present tab,
    returns a list of dictionaries with keys:
    number, description, input, prompt, active_models.
    Skips the first two rows (headers) and skips column A (index 0).
    """
    result = []
    
    # Debug print the data structure
    print(f"[DEBUG] Present tab data type: {type(tab_2d)}")
    if tab_2d:
        print(f"[DEBUG] First row type: {type(tab_2d[0])}")
        if tab_2d[0]:
            print(f"[DEBUG] First cell type: {type(tab_2d[0][0])}")
    
    for row in tab_2d[2:]:  # Skip first two rows
        if len(row) < 6:
            print(f"[DEBUG] Skipping row with insufficient columns: {row}")
            continue
            
        # Ensure all values are strings
        row_data = {
            "number": str(row[1]).strip() if row[1] else "",
            "description": str(row[2]).strip() if row[2] else "",
            "input": str(row[3]).strip() if row[3] else "",
            "prompt": str(row[4]).strip() if row[4] else "",
            "active_models": str(row[5]).strip() if row[5] else "",
        }
        print(f"[DEBUG] Processed row data: {row_data}")
        result.append(row_data)
        
    return result
