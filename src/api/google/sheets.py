import gspread
from typing import List, Optional, Dict
from gspread.exceptions import APIError, WorksheetNotFound
from googleapiclient.errors import HttpError, Error
from src.constants import OVERSEER_SHEET_ID as SHEET_ID
from googleapiclient.discovery import Resource

def write_cell_value(
    client: gspread.Client,
    value: str,
    sheet_tab: str = "CONTROL_PANEL",
    cell: str = "C2",
    sheet_id: str = SHEET_ID,
) -> None:
    """
    Writes a single value to a specified cell in a sheet tab.

    Args:
        client: gspread client.
        sheet_tab: Tab name to write to.
        cell: A1-style cell reference (e.g., 'C5').
        value: Value to write.
        sheet_id: ID of the Google Sheet.

    Raises:
        WorksheetNotFound: If sheet or worksheet not found
        HttpError: For HTTP errors (400, 401, 403, 404, 429, 500, 503)
        APIError: For other API errors
    """
    try:
        worksheet = client.open_by_key(sheet_id).worksheet(sheet_tab)
        worksheet.update_acell(cell, value)
        print(f"✅ Wrote '{value}' to {sheet_tab}!{cell}")
    except WorksheetNotFound as e:
        raise WorksheetNotFound(f"Worksheet '{sheet_tab}' not found in sheet {sheet_id}") from e
    except HttpError as e:
        raise
    except APIError as e:
        raise APIError(f"Failed to write to cell {cell}: {str(e)}") from e

def load_entire_tab(
    client: gspread.Client,
    sheet_tab: str = "CONTROL_PANEL",
    sheet_id: str = SHEET_ID,
) -> List[List[str]]:
    """
    Loads all values from the specified sheet tab.

    Args:
        client: gspread client instance.
        sheet_tab: Name of the tab to read from.
        sheet_id: ID of the spreadsheet.

    Returns:
        A list of rows, each row being a list of strings.

    Raises:
        WorksheetNotFound: If sheet or worksheet not found
        HttpError: For HTTP errors (400, 401, 403, 404, 429, 500, 503)
        APIError: For other API errors
    """
    try:
        print(f"[DEBUG] Opening spreadsheet ID: {sheet_id}")
        spreadsheet = client.open_by_key(sheet_id)

        print(f"[DEBUG] Accessing tab: '{sheet_tab}'")
        worksheet = spreadsheet.worksheet(sheet_tab)

        # Get all values as strings
        data = worksheet.get_all_values()
        
        # Debug print the data structure
        print(f"[DEBUG] Data type: {type(data)}")
        print(f"[DEBUG] First row type: {type(data[0]) if data else 'No data'}")
        print(f"[DEBUG] First cell type: {type(data[0][0]) if data and data[0] else 'No data'}")

        row_count = len(data)
        col_count = len(data[0]) if data else 0

        print(f"[DEBUG] Loaded {row_count} rows and {col_count} columns from tab '{sheet_tab}'")
        print("\n[DEBUG] Full tab data:")
        print("-" * 50)
        for i, row in enumerate(data):
            print(f"Row {i+1}: {row}")
        print("-" * 50)

        return data

    except WorksheetNotFound as e:
        raise WorksheetNotFound(f"Worksheet '{sheet_tab}' not found in sheet {sheet_id}") from e
    except HttpError as e:
        raise
    except APIError as e:
        raise APIError(f"Failed to load tab '{sheet_tab}': {str(e)}") from e

def get_cell_value_from_2d_list(data: List[List[str]], cell: str) -> str:
    """
    Given a 2D list (data) and a cell string like 'C1',
    return the value at that cell.
    """
    # Convert cell like 'C1' to row/col indexes
    col_letter = ''.join(filter(str.isalpha, cell)).upper()
    row_number = int(''.join(filter(str.isdigit, cell)))

    # Convert column letter(s) to 0-based index
    col_index = 0
    for i, char in enumerate(reversed(col_letter)):
        col_index += (ord(char) - ord('A') + 1) * (26 ** i)
    col_index -= 1  # 0-based

    # Row is also 0-based
    row_index = row_number - 1

    try:
        return data[row_index][col_index]
    except IndexError:
        raise ValueError(f"Cell {cell} is out of bounds in the provided data.")

def col_letter_to_index(col_letter: str) -> int:
    """
    Converts Excel-style column letter (e.g. 'A', 'B', ..., 'AA') to 0-based index.
    """
    col_letter = col_letter.upper()
    index = 0
    for i, char in enumerate(reversed(col_letter)):
        index += (ord(char) - ord('A') + 1) * (26 ** i)
    return index - 1  # convert to 0-based index

def get_column_after_row(
    data: List[List[str]],
    column_letter: str,
    start_row: int
) -> List[str]:
    """
    Extracts values from a given column in a 2D list starting from a given row.
    
    Args:
        data: 2D list of data.
        column_letter: Letter(s) of the column to extract (e.g., 'A', 'C', 'AA').
        start_row: Row number to start from (0-based).
    
    Returns:
        A list of strings from the column.
    """
    col_index = col_letter_to_index(column_letter)
    return [
        row[col_index]
        for row in data[start_row:]
        if len(row) > col_index
    ]

def get_sheet_tabs(client: gspread.Client, sheet_id: str) -> List[str]:
    """
    Returns a list of tab (sheet) names for the given Google Sheet.
    """
    spreadsheet = client.open_by_key(sheet_id)
    return [ws.title for ws in spreadsheet.worksheets()]

def download_all_tabs(client: gspread.Client, sheet_id: str) -> Dict[str, list]:
    """
    Downloads all tabs from a Google Sheet and returns a dict of tab_name -> 2D list.
    """
    tab_names = get_sheet_tabs(client, sheet_id)
    return {tab: load_entire_tab(client, tab, sheet_id) for tab in tab_names}