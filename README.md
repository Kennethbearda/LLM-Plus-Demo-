# LLM Plus — Multi-Model AI Aggregator (Demo)

This **demo repository** showcases the architecture and selected components of *LLM Plus*, a Python-based pipeline designed to route inputs through multiple LLM providers and aggregate their outputs into a single, consensus answer.

> **Models integrated in the full project:** OpenAI GPT, Anthropic Claude, Google Gemini, DeepSeek  
> This demo removes proprietary keys and sensitive data while preserving system structure and representative orchestration logic.

---

## Overview

LLM Plus is designed to evaluate and compare responses from multiple large language models (LLMs) and produce a consolidated result (e.g., via majority vote or similar aggregation strategies).  
This repository demonstrates the **core workflow, aggregation logic, and system design** without requiring credentials.

---

## My Role (Kenneth Beard)

- Co-developed backend integration and prompt-engineering flow  
- Built Google Sheets & Drive automation for file input and result output  
- Implemented aggregation logic to compute consensus solutions from model outputs  
- Helped design evaluation steps for output quality, consistency, and failure analysis  

---

## High-Level Workflow (Production Path)

1. User drops a text / PDF / image file into a Google Drive folder  
2. A script reads the file and prepares provider-specific prompts  
3. Multiple LLM providers are queried  
4. Outputs are normalized and passed to an **aggregator** to produce a final answer  
5. The final answer is written back to a **Google Sheet** cell for easy consumption  

> **Note:** In this demo repository, provider calls and Drive integrations may be stubbed or simulated.

---

## Tech Stack

- **Python**
- **FastAPI** (optional HTTP layer in production)
- **APIs:** OpenAI, Anthropic (Claude), Google Gemini, DeepSeek
- **Google Sheets & Drive API** (production path)
- **Pandas**
- **Pytest** (light testing)

---

## Running the Demo (Local)

This demo mode runs **without API keys or credentials**.

```bash
git clone https://github.com/Kennethbearda/LLM-Plus-Demo-.git
cd LLM-Plus-Demo-
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py --demo
---
**Kenneth Beard**  
LinkedIn: https://linkedin.com/in/ken-beard-8923a62b2  
Email: kennethbearda@gmail.com

