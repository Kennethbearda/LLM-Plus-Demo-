# LLM Plus — Multi‑Model AI Aggregator (Demo)

This **demo repo** showcases the architecture and selected components of *LLM Plus*, a Python-based pipeline that sends text/PDF/image inputs through multiple LLM providers and aggregates the results to produce a single, consensus answer.

> **Models integrated in the full project:** OpenAI GPT, Anthropic Claude, Google Gemini, DeepSeek  
> **This demo** removes proprietary keys and sensitive data while preserving structure and representative code.

## My Role (Kenneth Beard)
- Co-developed backend integration and prompt-engineering flow.
- Built the Google Sheets/Drive automation for file input and cell output.
- Implemented aggregation logic to compute the most common / consensus solution from model outputs.
- Helped design evaluation steps for quality and consistency.

## High-Level Workflow
1. User drops a file (text / PDF / image) into a Google Drive folder.
2. A script reads the file, prepares model-specific prompts, and calls multiple providers.
3. Outputs are normalized and passed to an **aggregator** to produce a final answer (e.g., majority vote).
4. The final answer is written back to a **Google Sheet** cell for easy consumption.

## Tech Stack
- **Python**, FastAPI (optional HTTP layer)
- **APIs:** OpenAI, Anthropic (Claude), Google Gemini, DeepSeek
- **Google Sheets & Drive API** for data ingress/egress
- **Pandas** for processing
- **Pytest** for simple tests

## Running the Demo (Local)
1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in placeholders if you want to test providers you have keys for.  
   **Do not commit real keys**.
4. Run a simple script (example):
   ```bash
   python main.py --demo
   ```

> Note: This is a **sanitized** demo and may include mock calls / stubs where the private repo contains full implementations.

## Repository Notes
- Sensitive files were removed: `.env`, `credentials_demo.json`, IDE artifacts, caches.
- Code comments may reference provider-specific logic that’s stubbed here.
- If you’re reviewing for contracting work: this repository demonstrates real-world prompt flow, multi-model orchestration, and result aggregation.

## License
Demo-only; not for production use. See `LICENSE` or contact me for details.

— Kenneth Beard  
LinkedIn: linkedin.com/in/ken-beard-8923a62b2  
Email: kennethbearda@gmail.com
