# src/services/models.py
import base64
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image
import fitz  # PyMuPDF for PDF processing

# For GPT:
import openai

# For Gemini:
import google.generativeai as genai

# For Claude:
from anthropic import Anthropic

from pathlib import Path
from typing import List, Dict

def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from PDF using PyMuPDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text as string
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"❌ Failed to extract text from PDF {pdf_path}: {e}")
        return ""

def call_models(
    clients: Dict[str, Any],
    model_string: str,
    prompt: str,
    question: str,
    files: List[str],
) -> str:
    """
    Unified model caller for GPT, Gemini, Claude.
    
    Args:
        clients: Dict with keys 'gpt', 'gemini', 'claude' and client objects
        model_string: e.g. 'gpt-4o', 'claude-3-sonnet', 'gemini-1.5-pro'
        prompt: Prompt string
        question: Additional question string
        files: List of file paths (strings)
        attachments: Ignored for now

    Returns:
        Model output string or error message
    """
    full_prompt = f"{prompt}\n\n{question}"
    file_paths = [Path(p) for p in files]

    try:
        if model_string.startswith("gpt"):
            if "gpt" not in clients:
                return "[Error: Missing OpenAI GPT client]"
            return call_gpt_model(clients["gpt"], model_string, full_prompt, attachments=file_paths)

        elif model_string.startswith("gemini"):
            if "gemini" not in clients:
                return "[Error: Missing Google Gemini client]"
            return call_gemini_model(clients["gemini"], model_string, full_prompt, attachments=file_paths)

        elif model_string.startswith("claude"):
            if "claude" not in clients:
                return "[Error: Missing Anthropic Claude client]"
            return call_claude_model(clients["claude"], model_string, full_prompt, attachments=file_paths)

        else:
            return f"[Error: Unknown model prefix in '{model_string}']"

    except Exception as e:
        return f"[Model call error: {e}]"

def call_gpt_model(
    client: Any,
    model_string: str,
    prompt: str,
    history: Optional[List[Dict[str, str]]] = None,
    attachments: Optional[List[Path]] = None
) -> str:
    """
    Calls OpenAI ChatCompletion with support for PDF files using GPT-4 Vision.
    Args:
        client: an openai.OpenAI instance (from auth_gpt())
        model_string: e.g. "gpt-4-vision-preview"
        prompt: the user prompt
        history: a list of {"role": "...", "content": "..."} dicts (optional)
        attachments: a list of file paths (PDF or image)
    Returns:
        The model's response text.
    """
    try:
        # Build base messages list
        messages = []
        
        # Add history if provided
        if isinstance(history, dict):
            # Convert dict history to proper message format
            for role, content in history.items():
                messages.append({
                    "role": "assistant" if role.startswith("gpt") else "user",
                    "content": content
                })
        elif isinstance(history, list):
            # History is already in proper format
            messages.extend(history)

        # Handle attachments if provided
        if attachments:
            for path in attachments:
                ext = path.suffix.lower()
                print(f"🔄 Processing attachment: {path} (type: {ext})")
                
                if ext == '.pdf':
                    try:
                        print(f"📄 Extracting text from PDF using PyMuPDF: {path}")
                        
                        # Extract text from PDF using PyMuPDF
                        pdf_text = extract_pdf_text(path)
                        if pdf_text.strip():
                            # Add extracted text to the prompt
                            enhanced_prompt = f"{prompt}\n\nPDF Content:\n{pdf_text}"
                            messages.append({"role": "user", "content": enhanced_prompt})
                            print(f"✅ PDF text extracted: {len(pdf_text)} characters")
                        else:
                            # Fallback to original prompt if no text extracted
                            messages.append({"role": "user", "content": prompt})
                            print(f"⚠️ No text extracted from PDF, using original prompt")
                        
                    except Exception as e:
                        print(f"❌ Failed to process PDF {path}: {e}")
                        messages.append({"role": "user", "content": f"[Failed to process PDF: {path.name}]"})
                elif ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    try:
                        # For images, encode as base64
                        with open(path, "rb") as image_file:
                            image_data = base64.b64encode(image_file.read()).decode('utf-8')
                        
                        # Determine MIME type
                        mime_type, _ = mimetypes.guess_type(str(path))
                        if not mime_type or not mime_type.startswith('image/'):
                            mime_type = f"image/{ext[1:]}"
                        
                        # Add image with proper vision format
                        messages.append({
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_data}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        })
                        print(f"✅ Image processed: {mime_type}")
                    except Exception as e:
                        print(f"❌ Failed to process image {path}: {e}")
                        messages.append({"role": "user", "content": f"[Failed to process image: {path.name}]"})
                else:
                    print(f"⚠️ Unsupported file type: {ext}")
                    messages.append({"role": "user", "content": prompt})
        else:
            # No attachments, just add the prompt
            messages.append({"role": "user", "content": prompt})

        # Call OpenAI with the prepared messages
        print(f"⏳ Sending prompt to model: {model_string}")
        print(f"📝 Message has {len(messages)} messages")
        
        response = client.chat.completions.create(
            model=model_string,
            messages=messages,
            max_tokens=4096
        )
        
        print("✅ GPT response received")
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ GPT API error: {e}")
        return f"[GPT Error: {e}]"


def call_gemini_model(
    client: Any,
    model_string: str,
    prompt: str,
    history: Optional[dict[str, str]] = None,  # Changed from List[str] to dict
    attachments: Optional[List[Path]] = None
) -> str:
    """
    Calls a Gemini model via the genai client.
    Args:
      client: a genai module or a preconfigured generative model instance
              (from auth_gemini())
      model_string: e.g. "gemini-1.5-flash", "gemini-1.5-pro", etc.
      prompt: the user prompt
      history: dict with optional prior output (optional)
      attachments: list of image/pdf Paths (optional)
    Returns:
      The model's response text.
    """
    
    # Build content parts list
    content = []
    
    # Add history if provided
    if isinstance(history, dict) and history:
        # Combine all values (model outputs) into a single context string
        combined_history = "\n\n".join(f"{k}: {v}" for k, v in history.items() if v.strip())
        content.append(f"Previous context:\n{combined_history}\n\n")

    # Add main prompt
    content.append(prompt)
    
    # Handle attachments
    if attachments:
        for path in attachments:
            ext = path.suffix.lower()
            print(f"🔄 Processing Gemini attachment: {path} (type: {ext})")
            
            if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                try:
                    # For images, use PIL to open and add to content
                    image = Image.open(path)
                    content.append(image)
                    print(f"✅ Image added to Gemini content: {path.name}")
                except Exception as e:
                    print(f"❌ Failed to process image {path}: {e}")
                    content.append(f"[Failed to load image: {path.name}]")
                    
            elif ext == ".pdf":
                try:
                    # Try to extract text first for better processing
                    pdf_text = extract_pdf_text(path)
                    if pdf_text.strip():
                        # Add extracted text to content
                        content.append({
                            "type": "text", 
                            "text": f"PDF Content:\n{pdf_text}\n"
                        })
                        print(f"✅ PDF text extracted: {len(pdf_text)} characters")
                    
                    # Also upload the PDF file for visual processing
                    uploaded_file = genai.upload_file(str(path))
                    content.append(uploaded_file)
                    print(f"✅ PDF uploaded to Gemini: {path.name}")
                except Exception as e:
                    print(f"❌ Failed to process PDF {path}: {e}")
                    content.append(f"[Failed to process PDF: {path.name}]")
            else:
                print(f"⚠️ Unsupported file type for Gemini: {ext}")
                content.append(f"[Unsupported file type: {path.name}]")
    
    try:
        print(f"⏳ Sending prompt to Gemini model: {model_string}")
        print(f"📝 Content items: {len(content)}")
        
        # Create the model instance
        model = genai.GenerativeModel(model_string)
        
        # Generate content
        response = model.generate_content(content)
        
        print("✅ Gemini response received.")
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return f"[Gemini Error: {e}]"


def call_claude_model(
    client: Any,
    model_string: str,
    prompt: str,
    history: Optional[dict[str, str]] = None,
    attachments: Optional[List[Path]] = None
) -> str:
    """
    Calls an Anthropic/Claude model with support for PDF and image attachments.
    
    Args:
        client: An Anthropic client instance (from auth_claude()).
        model_string: Model identifier (e.g., "claude-sonnet-4-20250514").
        prompt: The user prompt.
        history: List of previous messages (optional).
        attachments: List of PDF or image Paths (optional).
    
    Returns:
        The model's response text.
    """
    messages = []

    # 🧠 Add history if provided
    if isinstance(history, dict) and history:
        combined_history = "\n\n".join(f"{model}: {output}" for model, output in history.items() if output.strip())
        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": f"Previous context:\n{combined_history}\n"}]
        })

    # Prepare the current message content
    content = [{"type": "text", "text": prompt}]

    if attachments:
        for path in attachments:
            ext = path.suffix.lower()
            print(f"🔄 Processing attachment: {path} (type: {ext})")
            
            if ext == ".pdf":
                try:
                    # Try to extract text first for better processing
                    pdf_text = extract_pdf_text(path)
                    if pdf_text.strip():
                        # Add extracted text to content
                        content.append({
                            "type": "text", 
                            "text": f"PDF Content:\n{pdf_text}\n"
                        })
                        print(f"✅ PDF text extracted: {len(pdf_text)} characters")
                    
                    # Send PDF directly to Claude - it can read PDFs natively
                    with open(path, "rb") as pdf_file:
                        pdf_data = base64.b64encode(pdf_file.read()).decode('utf-8')
                    
                    content.append({
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    })
                    print(f"✅ PDF processed: {len(pdf_data)} base64 characters")
                except Exception as e:
                    content.append({"type": "text", "text": f"\n\n(Failed to process PDF at {path}: {e})"})
                    print(f"❌ PDF processing failed: {e}")
                    
            elif ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                try:
                    # Read and encode the image
                    with open(path, "rb") as image_file:
                        image_data = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # Determine MIME type
                    mime_type, _ = mimetypes.guess_type(str(path))
                    if not mime_type or not mime_type.startswith('image/'):
                        mime_type = f"image/{ext[1:]}"  # Remove the dot from extension
                    
                    # Add image to content
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_data
                        }
                    })
                    print(f"✅ Image processed: {mime_type}, {len(image_data)} base64 characters")
                    
                except Exception as e:
                    content.append({"type": "text", "text": f"\n\n(Failed to process image at {path}: {e})"})
                    print(f"❌ Image processing failed: {e}")
            else:
                content.append({"type": "text", "text": f"\n\n(Unsupported attachment type: {path})"})
                print(f"⚠️ Unsupported file type: {ext}")

    # Append the current message to messages
    messages.append({"role": "user", "content": content})

    print(f"⏳ Sending prompt to Claude model: {model_string}")
    print(f"📝 Message has {len(content)} content items")
    
    try:
        response = client.messages.create(
            model=model_string,
            messages=messages,
            max_tokens=4000  # Increased for longer responses
        )
        print("✅ Claude response received.")
        return response.content[0].text.strip()
    except Exception as e:
        print(f"❌ API call failed: {e}")
        raise