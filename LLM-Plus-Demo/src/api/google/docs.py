from typing import List, Dict, Optional
from googleapiclient.discovery import Resource
from services.constants import DOCUMENT_ID

def write_to_docs(docs: Resource, ledger: List[Dict[str, Optional[str]]]) -> None:
    """
    Writes each model’s outputs into the Google Doc specified by DOCUMENT_ID.
    Accepts ledger as List[Dict[str, Optional[str]]], where each entry is a dict
    mapping model names to that model’s latest output (which may be None).
    """
    requests = []
    # We'll insert newest entries at the top of the doc:
    for entry in reversed(ledger):
        for model, output in entry.items():
            if output is None:
                continue  # Skip if no output from model

            # Insert model heading
            requests.append({
                "insertText": {
                    "location": {"index": 1},
                    "text": f"## Results from {model}\n\n"
                }
            })
            # Insert model output
            requests.append({
                "insertText": {
                    "location": {"index": 1},
                    "text": output + "\n\n"
                }
            })

    if requests:
        docs.documents().batchUpdate(
            documentId=DOCUMENT_ID,
            body={"requests": requests}
        ).execute()